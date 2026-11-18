@echo off
rem 双击运行剪贴板绕过工具。默认拦截 Ctrl+V 并键入; 也可带参数:
rem   run.bat --diag   诊断: 枚举剪贴板所有格式并尝试解码
rem   run.bat --once   单次: 立即读一次剪贴板并打印来源格式/预览
if exist "D:\Python\python.exe" (
  "D:\Python\python.exe" "%~dp0clip_paste.py" %*
) else (
  python "%~dp0clip_paste.py" %*
)
if errorlevel 1 pause
