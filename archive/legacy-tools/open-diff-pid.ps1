$ErrorActionPreference = 'Stop'

$left  = 'D:\Codebuddy\backup\pid_tuner-20261028\pid_tuner.py'
$right = 'D:\bProject\pid_tuner\pid_tuner.py'

$exe = $null
$cands = @(
    'D:\Codebuddy\CodeBuddy CN\Code.exe',
    'D:\Codebuddy\CodeBuddy CN\CodeBuddy.exe',
    'D:\Vscode\Microsoft VS Code\Code.exe'
)
foreach ($c in $cands) {
    if (Test-Path $c) { $exe = $c; break }
}
if (-not $exe) {
    $f = Get-ChildItem 'D:\Codebuddy' -Recurse -Filter 'Code*.exe' -Depth 2 -ErrorAction SilentlyContinue |
         Select-Object -First 1
    if ($f) { $exe = $f.FullName }
}

Write-Output ('exe = ' + $exe)
if (-not $exe) { throw 'no editor exe found' }

Start-Process -FilePath $exe -ArgumentList '--diff', $left, $right
Write-Output 'diff window requested'
