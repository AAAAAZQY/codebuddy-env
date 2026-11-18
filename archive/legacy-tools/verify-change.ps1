$ErrorActionPreference = 'Stop'
$mirror = 'D:\plain_view\66T\mis-t160-main-ptz'
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$enc = [Text.Encoding]::GetEncoding(28591)

Start-Sleep -Seconds 3
foreach ($rel in @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')) {
    $mp = Join-Path $mirror $rel
    $mb = [IO.File]::ReadAllBytes($mp)
    $ms = $enc.GetString($mb)
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($rp)
    $tmp = [IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $u
    $rb = [IO.File]::ReadAllBytes($tmp)
    Remove-Item $tmp -Force
    $same = ($rb.Length -eq $mb.Length)
    if ($same) {
        for ($i = 0; $i -lt $mb.Length; $i++) { if ($rb[$i] -ne $mb[$i]) { $same = $false; break } }
    }
    $flag = ''
    if ($ms.Contains('IMU_UART_CH                 UART_CH_8')) { $flag += ' imu->UART8' }
    if ($ms.Contains('//uart_init(&g_uart_cfg[5]);')) { $flag += ' debug-disabled' }
    Write-Output ($rel + '  mirrorBytes=' + $mb.Length + '  realBytes=' + $rb.Length + '  mirrorEqualsReal=' + $same + $flag)
}
Write-Output 'VERIFY-CHANGE-DONE'
