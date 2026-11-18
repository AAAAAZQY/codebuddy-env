$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$list = @(
    'application\inc\motor.h',
    'application\motor.c',
    'application\motor_bldc.c',
    'application\motor_sensor.c',
    'application\ptz.c',
    'bsw\inc\types.h',
    'bsw\pid.c'
)
foreach ($p in $list) {
    $f = Join-Path $root $p
    $b = [IO.File]::ReadAllBytes($f)
    $n = [Math]::Min(16, $b.Length)
    $head = [Text.Encoding]::ASCII.GetString($b, 0, $n)
    $mod = (Get-Item $f).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
    Write-Output ($p + '  len=' + $b.Length + '  mtime=' + $mod + '  head=' + $head.TrimEnd())
}
Write-Output 'CHK-DONE'
