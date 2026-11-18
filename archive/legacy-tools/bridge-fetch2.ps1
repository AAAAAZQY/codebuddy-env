$ErrorActionPreference = 'Stop'
$real = 'd:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$out = 'D:\Codebuddy\tmp\main'
$list = @(
    'application\cmd_pelcod.c',
    'application\cmd_mytechu.c',
    'application\cmd.c',
    'application\EEPROM.c',
    'application\preset.c',
    'application\inc\cmd.h',
    'application\inc\Camera.h',
    'hal\hal_icm42688p.c',
    'hal\inc\hal_icm42688p.h',
    'application\inc\cfg_board.h'
)
foreach ($rel in $list) {
    $src = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($src)
    $dst = Join-Path $out $rel
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
    & curl.exe -s -o $dst $u
    Write-Output ($rel + '  len=' + (Get-Item $dst).Length)
}
Write-Output 'FETCH2-DONE'
