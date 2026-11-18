$ErrorActionPreference = 'Stop'
$real = 'd:\aMyProject\Project\MIS-T160\mian\mis-t160\ptz_source_code\source_code'
$bakRoot = 'D:\Codebuddy\backup\ai-comment-20261020'
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
    $bb = [IO.File]::ReadAllBytes((Join-Path $bakRoot $rel))
    $same = ($rb.Length -eq $bb.Length)
    $firstDiff = -1
    if ($same) {
        for ($i = 0; $i -lt $rb.Length; $i++) {
            if ($rb[$i] -ne $bb[$i]) { $same = $false; $firstDiff = $i; break }
        }
    } else {
        $n = [Math]::Min($rb.Length, $bb.Length)
        for ($i = 0; $i -lt $n; $i++) {
            if ($rb[$i] -ne $bb[$i]) { $firstDiff = $i; break }
        }
    }
    Write-Output ($rel + '  realVsBackup identical=' + $same + '  realLen=' + $rb.Length + '  bakLen=' + $bb.Length + '  firstDiff=' + $firstDiff)
}
Write-Output 'CMP-DONE'
