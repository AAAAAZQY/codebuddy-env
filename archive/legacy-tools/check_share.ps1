$base = '\\192.168.0.6\ptz\AF&PTZ共享目录\2-课题分享'
Write-Output ('base exists: ' + (Test-Path -LiteralPath $base))
if (Test-Path -LiteralPath $base) {
    Get-ChildItem -LiteralPath $base | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
    $foc = Join-Path $base '伺服FOC'
    Write-Output ('foc dir exists: ' + (Test-Path -LiteralPath $foc))
    if (Test-Path -LiteralPath $foc) {
        Get-ChildItem -LiteralPath $foc | Select-Object Name, Length | Format-Table -AutoSize
    }
}
$files = @(
    (Join-Path $base 'AF基础.pptx'),
    (Join-Path $base 'AI通识课-苑志强.pptx'),
    (Join-Path $base '步进电机及驱动.pptx'),
    (Join-Path $base '伺服FOC\FOC_SVPWM-杨锡豪.pptx')
)
foreach ($f in $files) {
    Write-Output ($f + '  ->  ' + (Test-Path -LiteralPath $f))
}
