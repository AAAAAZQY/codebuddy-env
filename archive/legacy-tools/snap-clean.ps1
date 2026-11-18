$ErrorActionPreference = 'Stop'
$indexPath = Join-Path $env:APPDATA 'CodeBuddy CN\User\globalStorage\local.diff-snap\snaps\index.json'
if (-not (Test-Path $indexPath)) { Write-Output 'no index'; exit 0 }
$raw = Get-Content $indexPath -Raw -Encoding UTF8
$obj = $raw | ConvertFrom-Json
$keep = [ordered]@{}
foreach ($p in $obj.PSObject.Properties) {
    $path = [string]$p.Value.fsPath
    if ($path -like '*Codebuddy\tmp\main_live*' -or $path -like '*Codebuddy\tmp\main\*') {
        Write-Output ('drop: ' + $path)
        continue
    }
    $keep[$p.Name] = $p.Value
}
($keep | ConvertTo-Json -Depth 8) | Set-Content -Path $indexPath -Encoding UTF8
Write-Output ('remaining entries: ' + $keep.Keys.Count)
Write-Output 'SNAP-CLEAN-DONE'
