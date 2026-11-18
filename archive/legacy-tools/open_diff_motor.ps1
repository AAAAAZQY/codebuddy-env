$before = 'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc_before.c'
$after  = 'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'

if (-not (Test-Path $before)) { throw 'before file missing' }

Start-Process -FilePath 'D:\Vscode\Microsoft VS Code\Code.exe' `
              -ArgumentList '--diff', $before, $after
Write-Output 'diff window requested'
