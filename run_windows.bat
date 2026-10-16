@echo off
cd /d "%~dp0"

rem Use the same Python selection logic as the previous wave normalized tool.
set "CONDA_PYTHON=%USERPROFILE%\miniconda3\envs\cell-counting\python.exe"
if exist "%CONDA_PYTHON%" (
  "%CONDA_PYTHON%" icp_wave_normalized.py
  goto done
)

where py >nul 2>nul
if not errorlevel 1 (
  py -c "import numpy,pandas,scipy,matplotlib" >nul 2>nul
  if not errorlevel 1 (
    py icp_wave_normalized.py
    goto done
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python -c "import numpy,pandas,scipy,matplotlib" >nul 2>nul
  if not errorlevel 1 (
    python icp_wave_normalized.py
    goto done
  )
)

echo No Python environment with numpy, pandas, scipy, and matplotlib was found.
echo Install the packages listed in requirements.txt, then run this file again.
:done
pause
