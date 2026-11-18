$ErrorActionPreference = 'Stop'
$mirror = 'D:\plain_view\66T\mis-t160-main-ptz'
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$list = @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')
foreach ($rel in $list) {
    $mb = [IO.File]::ReadAllBytes((Join-Path $mirror $rel))
    $b64 = [Convert]::ToBase64String($mb)
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/write?p=' + [uri]::EscapeDataString($rp)
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Body $b64 -Uri $u
    Write-Output ('push ' + $rel + '  ' + $resp.Content)
}
Write-Output 'PUSH-DONE'
