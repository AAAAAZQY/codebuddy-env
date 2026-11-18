$ErrorActionPreference = 'SilentlyContinue'
$roots = @(
    'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN',
    'C:\Users\myages2026\.codebuddycn',
    'C:\Users\myages2026\.codebuddy',
    'D:\Codebuddy'
)
$cut = (Get-Date).AddHours(-3)
foreach ($r in $roots) {
    Get-ChildItem $r -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt $cut } |
        Where-Object { $_.Length -lt 2MB } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 25 |
        ForEach-Object {
            Write-Output ($_.LastWriteTime.ToString('HH:mm:ss') + '  ' + $_.Length + '  ' + $_.FullName)
        }
}
Write-Output 'RECENT-DONE'
