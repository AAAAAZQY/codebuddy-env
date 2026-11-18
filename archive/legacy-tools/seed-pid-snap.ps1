$ErrorActionPreference = 'Stop'
$env:ELECTRON_RUN_AS_NODE = '1'

$left  = 'D:\Codebuddy\backup\pid_tuner-20261028\pid_tuner.py'
$right = 'D:\bProject\pid_tuner\pid_tuner.py'
$seeder = 'D:\Codebuddy\tools\seed-snap-any.js'

if (-not (Test-Path $left))  { throw 'left missing' }
if (-not (Test-Path $right)) { throw 'right missing' }

& 'D:\Vscode\Microsoft VS Code\Code.exe' $seeder $left $right
Write-Output ('exit=' + $LASTEXITCODE)

Start-Sleep -Milliseconds 800
$idx = Join-Path $env:APPDATA 'CodeBuddy CN\User\globalStorage\local.diff-snap\snaps\index.json'
if (Test-Path $idx) {
    $j = Get-Content $idx -Raw -Encoding UTF8 | ConvertFrom-Json
    $keys = $j.PSObject.Properties.Name
    Write-Output ('index entries: ' + $keys.Count)
    foreach ($k in $keys) {
        if ($k -like '*pid_tuner*') { Write-Output ('  hit: ' + $k) }
    }
} else {
    Write-Output 'index.json not found'
}
