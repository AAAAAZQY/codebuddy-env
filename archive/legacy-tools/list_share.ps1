$ErrorActionPreference = 'SilentlyContinue'
$out = 'D:\Codebuddy\tmp\share_tree.txt'
$lines = @()

$l1 = '\\192.168.0.6\ptz\AF&PTZ共享目录'
$lines += 'L1 exists: ' + (Test-Path -LiteralPath $l1)
if (Test-Path -LiteralPath $l1) {
    Get-ChildItem -LiteralPath $l1 | ForEach-Object {
        $lines += ('  [D] ' + $_.Name)
    }
}

$l2 = '\\192.168.0.6\ptz\AF&PTZ共享目录\2-课题分享'
$lines += 'L2 exists: ' + (Test-Path -LiteralPath $l2)
if (Test-Path -LiteralPath $l2) {
    Get-ChildItem -LiteralPath $l2 | ForEach-Object {
        if ($_.PSIsContainer) {
            $lines += ('  [D] ' + $_.Name)
            Get-ChildItem -LiteralPath $_.FullName | ForEach-Object {
                $lines += ('      - ' + $_.Name + '   ' + $_.Length)
            }
        } else {
            $lines += ('  [F] ' + $_.Name + '   ' + $_.Length)
        }
    }
}

$lines | Out-File -FilePath $out -Encoding utf8
Get-Content -LiteralPath $out
