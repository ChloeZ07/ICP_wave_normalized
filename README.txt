ICP WAVE NORMALIZED (NO ECG)

WINDOWS
-------
1. Double-click run_windows.bat.
2. Select one or more Cerelink-wave CSV files.
3. Results are saved in the result folder.

MAC
---
Before the first run:

1. Open Terminal.
2. Type "cd " with a space after cd.
3. Drag this program folder into Terminal and press Return.
4. Run:

   chmod +x run_mac.command

After that, double-click run_mac.command. Select one or more Cerelink-wave
CSV files. Results are saved in the result folder.

On the first Mac run, the program creates a local .venv and installs the
packages in requirements.txt. Internet access is needed for that first run.

FILES TO SELECT
---------------
Select Cerelink-wave CSV files, not Cerelink-trend files. You can select the
three representative one-hour files at the same time.

METHOD
------
1. Detect the main ICP pulse peaks from a 0.5-8 Hz filtered copy of ICP.
2. Use the trough between adjacent peaks as each pulse boundary.
3. Keep pulses lasting 0.40-1.50 seconds that do not cross a data gap.
4. Resample every accepted pulse to 101 points (0-100%).
5. Calculate mean ICP and SEM at every phase point.

The filtered signal is used only to find pulse boundaries. Mean and SEM use
the original ICP values. Because there is no ECG, the phase is ICP
pulse-to-pulse phase, not ECG R-to-R phase.

OUTPUT FOR EACH FILE
--------------------
- icp_normalized_waveform.csv
- icp_normalized_waveform.png
- icp_summary.txt

OUTPUT FOR MULTIPLE FILES
-------------------------
- comparison_normalized_waveforms.csv
- comparison_normalized_waveforms.png

The comparison files place the normalized mean waveforms from all selected
one-hour files together. The line is mean ICP and the shaded area is SEM.
