$roots = @('D:\plain_view', 'D:\bProject', 'D:\aMyProject', 'C:\Users\myages2026\Desktop')
foreach ($root in $roots) {
    if (Test-Path -LiteralPath $root) {
        Get-ChildItem -LiteralPath $root -Recurse -Filter 'pid_tuner.py' -ErrorAction SilentlyContinue |
            ForEach-Object {
                Write-Output ("{0}  {1} bytes  {2}" -f $_.FullName, $_.Length, $_.LastWriteTime)
            }
    }
}
Write-Output '--- done ---'
