$ErrorActionPreference = 'Continue'
$killed = 0
foreach ($p in Get-CimInstance Win32_Process) {
    if ($p.CommandLine -and ($p.CommandLine -match 'bridge-oneway\.js' -or $p.CommandLine -match 'toolbox\\bridge\.js')) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Output ('STOPPED pid=' + $p.ProcessId)
        $killed++
    }
}
if ($killed -eq 0) { Write-Output 'bridge not running' }
