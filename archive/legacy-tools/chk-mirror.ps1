$ErrorActionPreference = 'Stop'
$mirror = 'D:\plain_view\66T\mis-t160-main-ptz'
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$meta = Join-Path $mirror '.mirror-meta.json'
Write-Output '--- mirror meta ---'
if (Test-Path $meta) {
    $b = [IO.File]::ReadAllBytes($meta)
    $head = [Text.Encoding]::ASCII.GetString($b, 0, [Math]::Min(14, $b.Length))
    $enc = $head.StartsWith('%TSD-Header')
    Write-Output ('encrypted=' + $enc)
    if (-not $enc) { Get-Content $meta -Raw }
} else {
    Write-Output 'no .mirror-meta.json'
}

Write-Output '--- key files ---'
$list = @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')
foreach ($rel in $list) {
    $p = Join-Path $mirror $rel
    if (-not (Test-Path $p)) { Write-Output ($rel + '  MISSING in mirror'); continue }
    $b = [IO.File]::ReadAllBytes($p)
    $head = [Text.Encoding]::ASCII.GetString($b, 0, [Math]::Min(12, $b.Length))
    Write-Output ($rel + '  bytes=' + $b.Length + '  encrypted=' + $head.StartsWith('%TSD-Header'))

    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($rp)
    $tmp = [IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $u
    $rb = [IO.File]::ReadAllBytes($tmp)
    Remove-Item $tmp -Force
    $same = ($rb.Length -eq $b.Length)
    if ($same) {
        for ($i = 0; $i -lt $b.Length; $i++) { if ($rb[$i] -ne $b[$i]) { $same = $false; break } }
    }
    Write-Output ('   realBytes=' + $rb.Length + '  mirrorEqualsReal=' + $same)
}
Write-Output 'CHK-MIRROR-DONE'
