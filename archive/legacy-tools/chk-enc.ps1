$ErrorActionPreference = 'SilentlyContinue'
$paths = @(
    'C:\Users\myages2026\.codebuddy-bridge\filebridge-src\extension.js',
    'C:\Users\myages2026\.codebuddy-bridge\filebridge-src\package.json',
    'C:\Users\myages2026\.vscode\extensions\local.filebridge-0.0.1\extension.js',
    'C:\Users\myages2026\.vscode\extensions\local.filebridge-0.0.1\package.json'
)
foreach ($p in $paths) {
    if (-not (Test-Path $p)) { Write-Output ('MISSING ' + $p); continue }
    $b = [IO.File]::ReadAllBytes($p)
    $n = [Math]::Min(16, $b.Length)
    $head = [Text.Encoding]::ASCII.GetString($b, 0, $n)
    $enc = $head.StartsWith('%TSD-Header')
    Write-Output ($p + '  len=' + $b.Length + '  encrypted=' + $enc + '  head=' + $head.Replace("`r", ' ').Replace("`n", ' '))
}
Write-Output 'ENC-CHK-DONE'
