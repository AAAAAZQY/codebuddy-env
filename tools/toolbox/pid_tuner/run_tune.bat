@echo off
chcp 65001 >nul
cd /d D:\bProject\pid_tuner

if "%~1"=="" (
    echo.
    echo  Usage: drag a vofa hex/binary data file onto this .bat icon
    echo         (or run:  run_tune.bat  data.txt)
    echo.
    pause
    exit /b 1
)

echo.
echo  === PID speed-loop tuning (rule-based, dt=0.05s) ===
echo  file : %~1
echo  pid  : 0.7 / 0.01 / 0   (edit inside this .bat if changed)
echo.

python pid_tuner.py --csv "%~1" --dt 0.05 --current-pid "0.7,0.01,0" --vofa-map "y=0,r=1"

echo.
pause
