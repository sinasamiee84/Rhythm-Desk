import io
import base64
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, butter, filtfilt
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator


def _reset_file(file_obj):
    """اگر ورودی فایلِ باز باشد، آن را به ابتدای فایل برمی‌گرداند."""
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except (OSError, ValueError):
            pass


def bandpass_filter(signal, fs, lowcut=0.5, highcut=40.0, order=2):
    """فیلتر میان‌گذر برای حذف نویز Baseline Wander و نویز فرکانس بالا"""
    nyq = 0.5 * fs
    low = max(lowcut / nyq, 0.0001)
    high = min(highcut / nyq, 0.99)
    if low >= high:
        low = high * 0.1
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)


def analyze_ecg(file_obj, sampling_rate=250):
    """
    تابع جامع تحلیل ECG سازگار با ویوهای پروژه RhythmDesk
    """
    try:
        # ۱. تبدیل و اعتبارسنجی نرخ نمونه‌برداری
        try:
            actual_fs = int(round(float(sampling_rate)))
            if actual_fs <= 0:
                actual_fs = 250
        except (ValueError, TypeError):
            actual_fs = 250

        # تبدیل FieldFile جنگو به مسیر یا فایل بازشده
        if hasattr(file_obj, "path") and not isinstance(file_obj, (str, bytes, os.PathLike)):
            try:
                file_obj = file_obj.path
            except (ValueError, NotImplementedError):
                file_obj.open("rb")
                file_obj = file_obj.file

        _reset_file(file_obj)

        # ۲. خواندن فایل CSV یا TXT
        try:
            df = pd.read_csv(file_obj, sep=None, engine='python', comment='#')
        except Exception:
            _reset_file(file_obj)
            df = pd.read_csv(file_obj, sep=None, engine='python', header=None, comment='#')

        numeric_df = df.apply(pd.to_numeric, errors="coerce")
        numeric_cols = [
            col for col in numeric_df.columns
            if numeric_df[col].notna().any()
        ]

        if not numeric_cols:
            _reset_file(file_obj)
            df = pd.read_csv(file_obj, sep=None, engine='python', header=None, comment='#')
            numeric_df = df.apply(pd.to_numeric, errors="coerce")
            numeric_cols = [
                col for col in numeric_df.columns
                if numeric_df[col].notna().any()
            ]

        if not numeric_cols:
            return {
                "success": False,
                "error": "هیچ ستون عددی معتبری در فایل پیدا نشد.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "فایل فاقد داده عددی",
            }

        # ۳. تشخیص هوشمند ستون سیگنال
        signal_col = None
        preferred_words = ('ecg', 'signal', 'mv', 'volt', 'amplitude', 'lead', 'سیگنال')

        for col in numeric_cols:
            if any(w in str(col).lower() for w in preferred_words):
                signal_col = col
                break

        if signal_col is None:
            signal_col = numeric_cols[0]

        signal = numeric_df[signal_col].to_numpy(dtype=float)
        signal = signal[np.isfinite(signal)]

        if signal.size < actual_fs:
            return {
                "success": False,
                "error": "داده سیگنال برای تحلیل کمتر از یک ثانیه است.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "داده ناکافی",
            }

        # ۴. فیلتر کردن سیگنال
        try:
            clean_segment = bandpass_filter(signal, fs=actual_fs, lowcut=0.5, highcut=40.0)
        except Exception:
            clean_segment = signal - np.mean(signal)

        time = np.arange(len(clean_segment)) / actual_fs

        # ۵. تشخیص دقیق پیک‌های R
        min_distance = max(int(0.35 * actual_fs), 1)
        q75, q25 = np.percentile(clean_segment, [75, 25])
        iqr = q75 - q25
        height_threshold = np.median(clean_segment) + 1.1 * iqr
        prominence_threshold = max(0.1 * np.ptp(clean_segment), 0.25 * np.std(clean_segment))

        peaks, _ = find_peaks(
            clean_segment,
            distance=min_distance,
            height=height_threshold,
            prominence=prominence_threshold
        )

        if len(peaks) < 2:
            peaks, _ = find_peaks(
                clean_segment,
                distance=min_distance,
                prominence=prominence_threshold
            )

        if len(peaks) < 2:
            return {
                "success": False,
                "error": f"تعداد پیک‌های کافی با نرخ {actual_fs} Hz پیدا نشد.",
                "bpm": None,
                "status": "NOISE",
                "arrhythmia_type": "پیک‌های کافی پیدا نشد",
            }

        # ۶. محاسبه فواصل و ضربان قلب
        rr_intervals = np.diff(peaks) / actual_fs
        rr_intervals = rr_intervals[np.isfinite(rr_intervals) & (rr_intervals > 0)]

        if rr_intervals.size == 0:
            raise ValueError("فاصله معتبر بین پیک‌های R پیدا نشد.")

        avg_hr = float(60.0 / np.mean(rr_intervals))
        bpm = int(round(avg_hr))

        # ۷. تعیین وضعیت آریتمی سازگار با مدل دیتابیس (NORMAL یا ARRHYTHMIA)
        arrhythmias = []
        if 60 <= bpm <= 100:
            status = "NORMAL"
            arrhythmias.append("ریتم نرمال سینوسی (Normal Sinus Rhythm)")
        elif bpm > 100:
            status = "ARRHYTHMIA"
            arrhythmias.append("تاکی‌کاردی (Tachycardia - ضربان بالا)")
        else:
            status = "ARRHYTHMIA"
            arrhythmias.append("برادی‌کاردی (Bradycardia - ضربان پایین)")

        rr_cv = float(np.std(rr_intervals) / np.mean(rr_intervals)) if np.mean(rr_intervals) > 0 else 0
        if rr_cv > 0.09:
            arrhythmia_type = f"{arrhythmias[0]} | بی‌نظمی فواصل (Irregular RR)"
        else:
            arrhythmia_type = arrhythmias[0]

        # ۸. رسم نمودار استاندارد نوار قلب (جهت نمایش در صفحه جزئیات در صورت نیاز)
        fig, ax = plt.subplots(figsize=(11, 4), dpi=120)
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#fffbfc')

        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        ax.grid(which='major', color='#f5a9b8', linestyle='-', linewidth=0.8, alpha=0.8)
        ax.grid(which='minor', color='#fce4ec', linestyle=':', linewidth=0.5, alpha=0.9)

        ax.plot(time, clean_segment, label="Filtered ECG", color="#004d40", linewidth=1.3, zorder=3)
        ax.scatter(time[peaks], clean_segment[peaks], color="#d32f2f", s=35, edgecolors='black', linewidth=0.5,
                   label=f"R-peaks ({len(peaks)})", zorder=4)

        ax.set_title(f"ECG Analysis | FS: {actual_fs} Hz | BPM: {bpm}", fontsize=11, fontweight='bold', pad=10,
                     color='#212121')
        ax.set_xlabel("Time (seconds)", fontsize=9)
        ax.set_ylabel("Amplitude (mV)", fontsize=9)
        ax.set_xlim(0, max(time) if len(time) > 0 else 1)

        for spine in ax.spines.values():
            spine.set_color('#757575')
            spine.set_linewidth(0.8)

        ax.legend(loc="upper right", frameon=True, facecolor='white', framealpha=0.9, fontsize=8)
        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "success": True,
            "bpm": bpm,
            "status": status,
            "arrhythmia_type": arrhythmia_type,
            "plot_base64": image_base64,
            "num_peaks": len(peaks),
        }

    except Exception as exc:
        plt.close('all')
        return {
            "success": False,
            "error": f"خطا در پردازش سیگنال: {exc}",
            "bpm": None,
            "status": "NOISE",
            "arrhythmia_type": "تحلیل ناموفق",
        }
