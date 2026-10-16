"""Normalize Cerelink ICP pulses to 0-100% and calculate mean and SEM."""

from pathlib import Path
import sys
from tkinter import Tk, filedialog

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, find_peaks, sosfiltfilt


POINTS = 101
MIN_CYCLE = 0.40
MAX_CYCLE = 1.50


def choose_files():
    root = Tk()
    root.withdraw()
    names = filedialog.askopenfilenames(
        title="Select Cerelink WAVE CSV files",
        filetypes=[("CSV files", "*.csv")],
    )
    root.destroy()
    return [Path(name) for name in names]


def load_file(path):
    data = pd.read_csv(path, sep="\t")
    if "ICP [mmHg]" not in data.columns:
        raise ValueError("This is not a Cerelink wave CSV.")

    stamps = pd.to_datetime(
        data["Date"].astype(str) + " " + data["Time"].astype(str)
    )
    time = (stamps - stamps.iloc[0]).dt.total_seconds().to_numpy()
    icp = pd.to_numeric(data["ICP [mmHg]"], errors="coerce").to_numpy()
    fs = 1 / np.median(np.diff(time))

    if fs < 20:
        raise ValueError("Please select a wave file, not a trend file.")
    return time, icp, fs, stamps.iloc[0], stamps.iloc[-1]


def normalize_pulses(time, icp, fs):
    # Filtered ICP is used only to find pulse peaks and troughs.
    filled = pd.Series(icp).interpolate(limit_direction="both").to_numpy()
    sos = butter(3, [0.5, 8], btype="bandpass", fs=fs, output="sos")
    filtered = sosfiltfilt(sos, filled)

    iqr = np.percentile(filtered, 75) - np.percentile(filtered, 25)
    peaks, _ = find_peaks(
        filtered,
        distance=round(0.40 * fs),
        prominence=max(0.15, 0.35 * iqr),
    )

    # The trough between adjacent main peaks is the pulse boundary.
    troughs = []
    for left, right in zip(peaks[:-1], peaks[1:]):
        troughs.append(left + np.argmin(filtered[left:right + 1]))

    phase = np.linspace(0, 1, POINTS)
    pulses = []
    rejected = 0
    for left, right in zip(troughs[:-1], troughs[1:]):
        duration = time[right] - time[left]
        pulse = icp[left:right + 1]
        valid = (
            MIN_CYCLE <= duration <= MAX_CYCLE
            and len(pulse) >= 20
            and np.all(np.isfinite(pulse))
            and np.all(np.diff(time[left:right + 1]) <= 0.05)
        )
        if valid:
            old_phase = np.linspace(0, 1, len(pulse))
            pulses.append(np.interp(phase, old_phase, pulse))
        else:
            rejected += 1

    if not pulses:
        raise ValueError("No valid ICP pulses were found.")
    return np.asarray(pulses), peaks, rejected


def analyze_file(path, result_root):
    time, icp, fs, start, end = load_file(path)
    pulses, peaks, rejected = normalize_pulses(time, icp, fs)

    phase = np.linspace(0, 100, POINTS)
    mean = pulses.mean(axis=0)
    sem = pulses.std(axis=0, ddof=1) / np.sqrt(len(pulses))

    output = result_root / f"{path.stem}_icp_normalized"
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "phase_percent": phase,
        "mean_icp_mmHg": mean,
        "sem_icp_mmHg": sem,
    }).to_csv(output / "icp_normalized_waveform.csv", index=False)

    plt.figure(figsize=(9, 5))
    plt.fill_between(phase, mean - sem, mean + sem, alpha=0.25, label="Mean ± SEM")
    plt.plot(phase, mean, linewidth=2.5, label="Mean ICP")
    plt.title(
        "ICP pulse-to-pulse normalized mean waveform\n"
        f"{path.name}\n"
        f"{start:%Y-%m-%d %H:%M:%S} to {end:%H:%M:%S}",
        fontsize=12,
    )
    plt.xlabel("ICP pulse-cycle phase (%)")
    plt.ylabel("ICP (mmHg)")
    plt.grid(alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(output / "icp_normalized_waveform.png", dpi=180)
    plt.close()

    intervals = np.diff(time[peaks])
    intervals = intervals[(intervals >= MIN_CYCLE) & (intervals <= MAX_CYCLE)]
    median_interval = np.median(intervals)
    summary = (
        f"Source: {path.name}\n"
        f"Recording: {start} to {end}\n"
        f"Sampling rate: {fs:.2f} Hz\n"
        f"Detected peaks: {len(peaks)}\n"
        f"Accepted pulses: {len(pulses)}\n"
        f"Rejected pulses: {rejected}\n"
        f"Median pulse interval: {median_interval:.3f} s\n"
        f"Estimated pulse rate: {60 / median_interval:.1f} bpm\n\n"
        "Method: ICP trough-to-trough pulses were resampled to 101 points "
        "(0-100%), then mean and SEM were calculated at every phase point.\n"
    )
    (output / "icp_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    label = (
        f"{path.name}\n"
        f"{start:%Y-%m-%d %H:%M:%S} to {end:%H:%M:%S}"
    )
    return label, phase, mean, sem


def save_comparison(results, result_root):
    if len(results) < 2:
        return

    table = {"phase_percent": results[0][1]}
    plt.figure(figsize=(10, 5.8))
    for number, (label, phase, mean, sem) in enumerate(results, 1):
        plt.plot(phase, mean, linewidth=2, label=label)
        plt.fill_between(phase, mean - sem, mean + sem, alpha=0.12)
        table[f"period_{number}_mean_icp_mmHg"] = mean
        table[f"period_{number}_sem_icp_mmHg"] = sem

    plt.title("ICP normalized mean waveforms by one-hour period")
    plt.xlabel("ICP pulse-cycle phase (%)")
    plt.ylabel("ICP (mmHg)")
    plt.grid(alpha=0.25)
    plt.legend(frameon=False, fontsize=8)
    plt.tight_layout()
    plt.savefig(result_root / "comparison_normalized_waveforms.png", dpi=180)
    plt.close()
    pd.DataFrame(table).to_csv(
        result_root / "comparison_normalized_waveforms.csv", index=False
    )


def main():
    files = [Path(name) for name in sys.argv[1:]] or choose_files()
    if not files:
        return

    result_root = Path(__file__).resolve().parent / "result"
    result_root.mkdir(exist_ok=True)
    results = []

    for path in files:
        print(f"Analyzing {path.name} ...")
        try:
            results.append(analyze_file(path, result_root))
        except Exception as error:
            print(f"Skipped: {error}\n")

    save_comparison(results, result_root)
    print(f"Finished. Results saved in: {result_root}")


if __name__ == "__main__":
    main()
