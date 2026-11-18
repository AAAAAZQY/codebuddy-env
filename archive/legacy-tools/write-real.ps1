$ErrorActionPreference = 'Stop'
$real = 'd:\aMyProject\Project\MIS-T160\mian\mis-t160\ptz_source_code\source_code'
$mirror = 'd:\plain_view\66T\mis-t160-XH-ptz'
$list = @(
    'application\inc\motor.h',
    'application\motor.c',
    'application\motor_bldc.c',
    'application\motor_sensor.c',
    'application\ptz.c',
    'bsw\inc\types.h',
    'bsw\pid.c'
)
foreach ($rel in $list) {
    $mb = [IO.File]::ReadAllBytes((Join-Path $mirror $rel))
    $b64 = [Convert]::ToBase64String($mb)
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/write?p=' + [uri]::EscapeDataString($rp)
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Body $b64 -Uri $u
    Write-Output ($rel + '  write=' + $resp.Content + '  sent=' + $mb.Length)
}
Write-Output 'WRITE-DONE'
