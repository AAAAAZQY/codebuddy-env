$env:ELECTRON_RUN_AS_NODE = '1'
$exe = 'D:\Vscode\Microsoft VS Code\Code.exe'
$js = 'D:\Codebuddy\tools\deploy-ext.js'
$log = 'D:\Codebuddy\tools\deploy-ext.log'
if (Test-Path $log) { Remove-Item $log -Force }
& $exe $js
Start-Sleep -Seconds 3
if (Test-Path $log) {
    Get-Content $log
} else {
    Write-Output 'NO-LOG (script did not run)'
}
