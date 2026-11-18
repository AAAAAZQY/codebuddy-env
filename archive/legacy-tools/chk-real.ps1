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
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($rp)
    $tmp = [IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $u
    $rb = [IO.File]::ReadAllBytes($tmp)
    Remove-Item $tmp -Force
    $mb = [IO.File]::ReadAllBytes((Join-Path $mirror $rel))
    $rtxt = [Text.Encoding]::GetEncoding(936).GetString($rb)
    $hasAi = $rtxt.Contains('[AI-COMMENT]')
    $equal = ($rb.Length -eq $mb.Length)
    if ($equal) {
        for ($i = 0; $i -lt $rb.Length; $i++) {
            if ($rb[$i] -ne $mb[$i]) { $equal = $false; break }
        }
    }
    Write-Output ($rel + '  realLen=' + $rb.Length + '  mirrorLen=' + $mb.Length + '  realHasAI=' + $hasAi + '  identical=' + $equal)
}
Write-Output 'REAL-CHK-DONE'
