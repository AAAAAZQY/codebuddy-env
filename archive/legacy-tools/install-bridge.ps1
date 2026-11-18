$ErrorActionPreference = 'Stop'
$src = 'C:\Users\myages2026\AppData\Local\Temp\bridge_new.js'
$dst = 'C:\Users\myages2026\.codebuddy-bridge\bridge.js'
$bkp = 'D:\Codebuddy\backup\bridge.js.' + (Get-Date -Format 'yyyyMMdd-HHmmss')

New-Item -ItemType Directory -Path 'D:\Codebuddy\backup' -Force | Out-Null
Copy-Item $src $bkp -Force
Write-Host ('backup -> ' + $bkp + ' (' + (Get-Item $bkp).Length + 'B)')

$bytes = [IO.File]::ReadAllBytes($src)
Write-Host ('new bridge.js = ' + $bytes.Length + 'B')

$b64 = [Convert]::ToBase64String($bytes)
$r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri ('http://127.0.0.1:37821/write?p=' + [uri]::EscapeDataString($dst)) -Body $b64 -ContentType 'text/plain'
Write-Host ('install resp: ' + $r.Content)

Start-Sleep -Milliseconds 500
$chk = 'C:\Users\myages2026\AppData\Local\Temp\bridge_chk.js'
Invoke-WebRequest -UseBasicParsing -Uri ('http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($dst)) -OutFile $chk
$h1 = (Get-FileHash $src -Algorithm SHA256).Hash
$h2 = (Get-FileHash $chk -Algorithm SHA256).Hash
Write-Host ('installed size=' + (Get-Item $chk).Length + ' identical=' + ($h1 -eq $h2))
Remove-Item $chk -Force
