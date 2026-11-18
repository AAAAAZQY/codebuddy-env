@echo off

chcp 65001 >nul
setlocal

set PYFILE=D:\Codebuddy\toolbox\vofa_report.py

if "%~1"=="" (
    echo ==========================================================
    echo   vofa 数据分析 - 读剪贴板
    echo ==========================================================
    echo   [1] 先在 vofa / 串口助手复制 hex 数据
    echo   [2] 按任意键开始分析
    echo.
    pause >nul
    python "%PYFILE%"
) else (
    python "%PYFILE%" %*
)

echo.
pause
