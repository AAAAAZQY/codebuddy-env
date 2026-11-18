$ErrorActionPreference = 'Stop'
$real = 'd:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$out = 'D:\Codebuddy\tmp\main'
$list = @(
    'application\motor_bldc.c',
    'application\ptz.c',
    'application\cmd_imu5146.c',
    'application\karlman.c',
    'application\cfg_board.c',
    'application\cfg_mcu.c',
    'application\main.c',
    'application\inc\motor.h',
    'application\inc\cmd_imu5146.h',
    'application\inc\karlman.h',
    'application\inc\includes.h',
    'application\inc\cfg_mcu.h',
    'application\inc\cfg_machine.h',
    'application\inc\EEPROM.h',
    'application\camera_helper.c',
    'bsw\pid.c',
    'bsw\utils.c',
    'bsw\inc\pid.h',
    'bsw\inc\utils.h',
    'bsw\inc\types.h',
    'hal\hal_stm32f429_uart.c',
    'hal\inc\hal_stm32f429_uart.h',
    'hal\hal_stm32f429_dma.c',
    'hal\inc\hal_stm32f429_dma.h'
)
foreach ($rel in $list) {
    $src = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($src)
    $dst = Join-Path $out $rel
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
    & curl.exe -s -o $dst $u
    $len = (Get-Item $dst).Length
    $n = [Math]::Min(12, $len)
    $head = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($dst), 0, $n)
    Write-Output ($rel + '  len=' + $len + '  head=' + $head.Replace("`r", ' ').Replace("`n", ' '))
}
Write-Output 'FETCH-DONE'
