$ErrorActionPreference = 'SilentlyContinue'

Write-Output '--- Code.exe processes ---'
Get-CimInstance Win32_Process -Filter "Name='Code.exe'" | ForEach-Object {
    $cl = $_.CommandLine
    $kind = 'main'
    if ($cl -like '*extensionHost*') { $kind = 'extensionHost' }
    elseif ($cl -like '*--type=renderer*') { $kind = 'renderer' }
    elseif ($cl -like '*--type=gpu*') { $kind = 'gpu' }
    elseif ($cl -like '*--type=utility*') { $kind = 'utility' }
    $st = ([Management.ManagementDateTimeConverter]::ToDateTime($_.CreationDate))
    Write-Output ('pid=' + $_.ProcessId + '  ' + $kind + '  start=' + $st.ToString('yyyy-MM-dd HH:mm:ss'))
}

Write-Output ''
Write-Output '--- extension file ---'
$f = 'C:\Users\myages2026\.vscode\extensions\local.filebridge-0.0.1\extension.js'
$item = Get-Item $f
Write-Output ('mtime=' + $item.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') + '  diskBytes=' + $item.Length)

Write-Output ''
Write-Output '--- latest vscode log dirs ---'
$logRoot = 'C:\Users\myages2026\AppData\Roaming\Code\logs'
Get-ChildItem $logRoot -Directory | Sort-Object Name -Descending | Select-Object -First 3 | ForEach-Object {
    Write-Output ('dir: ' + $_.Name)
}

Write-Output ''
Write-Output '--- grep name-15 / Local File Bridge in newest exthost logs ---'
$newest = Get-ChildItem $logRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
if ($newest) {
    Get-ChildItem $newest.FullName -Recurse -Filter 'exthost*.log' | ForEach-Object {
        $txt = [IO.File]::ReadAllText($_.FullName)
        if ($txt.Length -gt 0) {
            $hit15 = $txt.Contains('name-15')
            $hit14 = $txt.Contains('name-14')
            Write-Output ('  ' + $_.FullName.Substring($logRoot.Length) + '  size=' + $txt.Length + '  name-15=' + $hit15 + '  name-14=' + $hit14 + '  head=' + $txt.Substring(0, [Math]::Min(60, $txt.Length)).Replace("`r", ' ').Replace("`n", ' '))
        }
    }
}
Write-Output 'CHK-SYNC-DONE'
