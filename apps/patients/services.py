import numpy as np
import pandas as pd


def _read_ecg_file(file_obj):
    """خواندن CSV یا TXT و پیدا کردن اولین ستون عددیِ سیگنال."""

    # اگر فایل قبلاً خوانده شده، از ابتدا بخوان
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    # تلاش اول: CSV با سرستون
    try:
        df = pd.read_csv(file_obj)
    except Exception:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        # فایل بدون سرستون
        df = pd.read_csv(file_obj, header=None)

    # اگر هیچ ستون عددی تشخیص داده نشد، فایل را بدون header امتحان کن
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)

        df = pd.read_csv(file_obj, header=None, sep=None, engine="python")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        raise ValueError(
            "هیچ ستون عددی در فایل پیدا نشد. فایل باید CSV/TXT و دارای داده عددی باشد."
        )

    # ترجیح ستون‌هایی با نام مرتبط با ECG
    signal_col = None
    preferred_words = ("ecg", "signal", "mv", "voltage", "amplitude")

    for col in numeric_cols:
        if any(word in str(col).lower() for word in preferred_words):
            signal_col = col
            break

    if signal_col is None:
        signal_col = numeric_cols[0]

    signal = pd.to_numeric(df[signal_col], errors="coerce").to_numpy(dtype=float)
    signal = signal[np.isfinite(signal)]

    if len(signal) == 0:
        raise ValueError("ستون سیگنال داده عددی معتبر ندارد.")

    return signal


def filter_signal(signal, sampling_rate):
    """حذف میانگین و فیلتر نرم‌کنندهٔ ساده."""
    signal = np.asarray(signal, dtype=float)

    if len(signal) < 3:
        raise ValueError("تعداد نمونه‌های سیگنال کافی نیست.")

    filtered = signal - np.mean(signal)

    window = max(1, int(sampling_rate / 100))
    window = min(window, len(filtered))

    kernel = np.ones(window, dtype=float) / window
    return np.convolve(filtered, kernel, mode="same")


def detect_r_peaks(signal, sampling_rate):
    """تشخیص سادهٔ پیک‌های R با آستانه و فاصلهٔ حداقلی."""
    signal = np.asarray(signal, dtype=float)

    if len(signal) < 3 or np.max(np.abs(signal)) == 0:
        return []

    threshold = 0.6 * np.max(np.abs(signal))
    min_distance = max(1, int(0.2 * sampling_rate))

    peaks = []

    for i in range(1, len(signal) - 1):
        if (
            signal[i] > threshold
            and signal[i] >= signal[i - 1]
            and signal[i] >= signal[i + 1]
        ):
            if peaks and i - peaks[-1] < min_distance:
                if signal[i] > signal[peaks[-1]]:
                    peaks[-1] = i
            else:
                peaks.append(i)

    return peaks


def analyze_ecg(file_obj, sampling_rate):
    """تحلیل مقدماتی ECG و برگرداندن BPM و وضعیت سیگنال."""

    try:
        sampling_rate = float(sampling_rate)

        if not np.isfinite(sampling_rate) or sampling_rate <= 0:
            raise ValueError("نرخ نمونه‌برداری باید عددی و بزرگ‌تر از صفر باشد.")

        signal = _read_ecg_file(file_obj)

        if len(signal) < sampling_rate:
            return {
                "success": False,
                "error": "داده سیگنال برای تحلیل کمتر از یک ثانیه است.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "داده ناکافی",
            }

        filtered = filter_signal(signal, sampling_rate)
        peaks = detect_r_peaks(filtered, sampling_rate)

        if len(peaks) < 2:
            return {
                "success": False,
                "error": "برای محاسبه ضربان، حداقل دو پیک R لازم است.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "پیک‌های کافی پیدا نشد",
            }

        rr_intervals = np.diff(peaks) / sampling_rate
        rr_intervals = rr_intervals[rr_intervals > 0]

        if len(rr_intervals) == 0:
            raise ValueError("فاصلهٔ معتبر بین پیک‌های R پیدا نشد.")

        bpm = int(round(60 / np.mean(rr_intervals)))

        if 60 <= bpm <= 100:
            status = "NORMAL"
            arrhythmia_type = "نرمال"
        elif bpm > 100:
            status = "ARRHYTHMIA"
            arrhythmia_type = "تاکیکاردی (ضربان زیاد)"
        else:
            status = "ARRHYTHMIA"
            arrhythmia_type = "برادیکاردی (ضربان کم)"

        return {
            "success": True,
            "bpm": bpm,
            "status": status,
            "arrhythmia_type": arrhythmia_type,
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"خطا در تحلیل فایل: {exc}",
            "bpm": None,
            "status": "NOISE",
            "arrhythmia_type": "تحلیل ناموفق",
        }
