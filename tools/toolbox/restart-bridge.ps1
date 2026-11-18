& 'D:\Codebuddy\toolbox\bridge-stop.ps1'
Start-Sleep -Seconds 2
Start-Process -FilePath 'D:\Codebuddy\toolbox\bridge-start.cmd' -WindowStyle Hidden
$ok = $false
for ($i = 0; $i -lt 12 -and -not $ok; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:37821/ping' -TimeoutSec 4
        Write-Host ('ping ok after ' + (($i + 1) * 2) + 's, pid=' + (ConvertFrom-Json $r.Content).pid)
        $ok = $true
    } catch {
        if ($i -eq 11) { Write-Host ('PING FAILED: ' + $_.Exception.Message) }
    }
}
