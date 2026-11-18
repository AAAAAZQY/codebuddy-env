$ErrorActionPreference = 'SilentlyContinue'
$cands = @(
    'D:\plain_view\66T\mis-t160-main-ptz\.codebuddy',
    'D:\plain_view\66T\mis-t160-main-ptz\.codebuddy\rules',
    'D:\plain_view\66T\mis-t160-main-ptz\CODEBUDDY.md',
    'D:\plain_view\66T\mis-t160-main-ptz\AGENTS.md',
    'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN\User\rules',
    'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN\User\.codebuddy',
    'C:\Users\myages2026\.codebuddy',
    'C:\Users\myages2026\.codebuddy\rules'
)
foreach ($p in $cands) {
    if (Test-Path $p) {
        Write-Output ('EXISTS  ' + $p)
        Get-ChildItem $p -ErrorAction SilentlyContinue | Select-Object -First 10 | ForEach-Object {
            Write-Output ('        ' + $_.Name)
        }
    } else {
        Write-Output ('MISSING ' + $p)
    }
}
Write-Output '--- search RULE.mdc anywhere under user profile codebuddy dirs ---'
foreach ($root in @('C:\Users\myages2026\.codebuddy', 'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN\User')) {
    Get-ChildItem $root -Recurse -Filter 'RULE.mdc' -ErrorAction SilentlyContinue | Select-Object -First 10 | ForEach-Object {
        Write-Output ('  ' + $_.FullName)
    }
}
Write-Output 'CHK-RULES-DONE'
