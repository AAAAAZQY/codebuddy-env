@echo off
chcp 65001 >nul
cd /d "%~dp0"
python pid_tuner.py %*
if errorlevel 1 pause
