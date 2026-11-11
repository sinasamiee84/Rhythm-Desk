import os

import numpy as np
import pandas as pd


def _reset_file(file_obj):
    """اگر ورودی فایلِ باز باشد، آن را به ابتدای فایل برمی‌گرداند."""
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except (OSError, ValueError):
            pass


def _read_ecg_file(file_obj):
    """
    خواندن CSV/TXT و استخراج یک ستون عددی از سیگنال.

    file_obj می‌تواند یکی از این‌ها باشد:
    - مسیر فایل به شکل str یا Path
    - فایل بازشده
    - فیلد فایل Django مثل record.signal_file
    """

    # تبدیل FieldFile جنگو به مسیر یا فایل بازشده
    if hasattr(file_obj, "path") and not isinstance(file_obj, (str, bytes, os.PathLike)):
        try:
            file_obj = file_obj.path
        except (ValueError, NotImplementedError):
            # در بعضی storageها path وجود ندارد؛ از خود فایل استفاده می‌کنیم
            file_obj.open("rb")
            file_obj = file_obj.file

    _reset_file(file_obj)

    # ابتدا فایل را به‌صورت CSV با جداکنندهٔ خودکار می‌خوانیم.
    # این کار برای comma، semicolon و tab مناسب است.
    try:
        df = pd.read_csv(
            file_obj,
            sep=None,
            engine="python",
            comment="#",
        )
    except Exception:
        _reset_file(file_obj)
        df = pd.read_csv(
            file_obj,
            sep=None,
            engine="python",
            header=None,
            comment="#",
        )

    # تبدیل ستون‌ها به عدد؛ متن‌ها به NaN تبدیل می‌شوند.
    numeric_df = df.apply(pd.to_numeric, errors="coerce")

    # ستون‌هایی که دست‌کم یک مقدار عددی دارند
    numeric_cols = [
        col for col in numeric_df.columns
        if numeric_df[col].notna().any()
    ]

    # اگر CSV با header خوانده شده ولی داده‌ها همگی زیر عنوان افتاده‌اند،
    # دوباره بدون header می‌خوانیم.
    if not numeric_cols:
        _reset_file(file_obj)
        df = pd.read_csv(
            file_obj,
            sep=None,
            engine="python",
            header=None,
            comment="#",
        )
        numeric_df = df.apply(pd.to_numeric, errors="coerce")
        numeric_cols = [
            col for col in numeric_df.columns
            if numeric_df[col].notna().any()
        ]

    if not numeric_cols:
        raise ValueError(
            "هیچ دادهٔ عددی در فایل پیدا نشد. فایل باید CSV یا TXT و دارای سیگنال عددی باشد."
        )

    # اگر نام ستون به سیگنال ECG اشاره کند، همان ستون را انتخاب می‌کنیم.
    preferred_words = ("ecg", "signal", "mv", "voltage", "amplitude")
    signal_col = next(
        (
            col for col in numeric_cols
            if any(word in str(col).lower() for word in preferred_words)
        ),
        numeric_cols[0],
    )

    signal = numeric_df[signal_col].to_numpy(dtype=float)
    signal = signal[np.isfinite(signal)]

    if signal.size == 0:
        raise ValueError("ستون انتخاب‌شده هیچ نمونهٔ عددی معتبری ندارد.")

    return signal


def filter_signal(signal, sampling_rate):
    """
    حذف میانگین و کاهش نویز ساده.

    توجه: این فیلتر یک فیلتر تشخیصیِ بالینی نیست؛ برای پردازش مقدماتی است.
    """
    signal = np.asarray(signal, dtype=float)

    if signal.ndim != 1 or signal.size < 3:
        raise ValueError("سیگنال باید حداقل سه نمونهٔ عددی داشته باشد.")

    if not np.all(np.isfinite(signal)):
        signal = signal[np.isfinite(signal)]

    if signal.size < 3:
        raise ValueError("نمونه‌های معتبر سیگنال کافی نیستند.")

    # حذف بایاس DC
    filtered = signal - np.mean(signal)

    # میانگین‌گیری کوتاه؛ اندازهٔ پنجره حداکثر برابر طول سیگنال است.
    window = max(1, int(round(sampling_rate / 100)))
    window = min(window, filtered.size)

    kernel = np.ones(window, dtype=float) / window
    return np.convolve(filtered, kernel, mode="same")


def detect_r_peaks(signal, sampling_rate):
    """
    تشخیص مقدماتی پیک‌های R با آستانهٔ نسبی و فاصلهٔ حداقلی.

    برای کاربرد پزشکی واقعی باید الگوریتم با دادهٔ معتبر ارزیابی شود.
    """
    signal = np.asarray(signal, dtype=float)

    if signal.ndim != 1 or signal.size < 3:
        return []

    max_amplitude = float(np.max(np.abs(signal)))
    if not np.isfinite(max_amplitude) or max_amplitude == 0:
        return []

    # آستانهٔ نسبی بر اساس دامنهٔ سیگنال
    threshold = 0.6 * max_amplitude

    # فاصلهٔ حداقلی 200 میلی‌ثانیه بین پیک‌ها
    min_distance = max(1, int(round(0.2 * sampling_rate)))

    peaks = []

    for i in range(1, signal.size - 1):
        is_peak = (
            signal[i] > threshold
            and signal[i] >= signal[i - 1]
            and signal[i] >= signal[i + 1]
        )

        if not is_peak:
            continue

        if peaks and i - peaks[-1] < min_distance:
            # اگر دو پیک خیلی نزدیک باشند، پیک بلندتر نگه داشته می‌شود.
            if signal[i] > signal[peaks[-1]]:
                peaks[-1] = i
        else:
            peaks.append(i)

    return peaks


def analyze_ecg(file_obj, sampling_rate):
    """
    تحلیل مقدماتی فایل ECG.

    خروجی موفق:
    {
        "success": True,
        "bpm": عدد,
        "status": "NORMAL" یا "ARRHYTHMIA",
        "arrhythmia_type": متن
    }

    خروجی ناموفق شامل success=False و error است.
    """

    try:
        sampling_rate = float(sampling_rate)

        if not np.isfinite(sampling_rate) or sampling_rate <= 0:
            raise ValueError(
                "نرخ نمونه‌برداری باید عددی و بزرگ‌تر از صفر باشد؛ مثلاً 250."
            )

        signal = _read_ecg_file(file_obj)

        # حداقل یک ثانیه سیگنال برای ادامهٔ تحلیل
        if signal.size < sampling_rate:
            return {
                "success": False,
                "error": "مدت سیگنال کمتر از یک ثانیه است؛ دادهٔ بیشتری لازم است.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "داده ناکافی",
            }

        filtered = filter_signal(signal, sampling_rate)
        peaks = detect_r_peaks(filtered, sampling_rate)

        if len(peaks) < 2:
            return {
                "success": False,
                "error": "کمتر از دو پیک R پیدا شد؛ محاسبهٔ ضربان ممکن نیست.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "پیک‌های کافی پیدا نشد",
            }

        # فاصلهٔ پیک‌های متوالی، بر حسب ثانیه
        rr_intervals = np.diff(peaks).astype(float) / sampling_rate
        rr_intervals = rr_intervals[
            np.isfinite(rr_intervals) & (rr_intervals > 0)
        ]

        if rr_intervals.size == 0:
            raise ValueError("فاصلهٔ معتبر بین پیک‌های R پیدا نشد.")

        mean_rr = float(np.mean(rr_intervals))
        bpm = int(round(60.0 / mean_rr))

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
