$ErrorActionPreference = 'Stop'
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$base = 'D:\Codebuddy\tmp\main'
$list = @(
    'application\inc\cfg_mcu.h',
    'application\cfg_mcu.c'
)
foreach ($rel in $list) {
    $lb = [IO.File]::ReadAllBytes((Join-Path $base $rel))
    $b64 = [Convert]::ToBase64String($lb)
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/write?p=' + [uri]::EscapeDataString($rp)
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Body $b64 -Uri $u
    Write-Output ('restore ' + $rel + '  ' + $resp.Content)
}
Write-Output 'RESTORE-WRITTEN'
