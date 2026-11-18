$ErrorActionPreference = 'Stop'
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$base = 'D:\Codebuddy\tmp\main'
$list = @(
    'application\inc\cfg_mcu.h',
    'application\cfg_mcu.c'
)
foreach ($rel in $list) {
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($rp)
    $tmp = [IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $u
    $rb = [IO.File]::ReadAllBytes($tmp)
    Remove-Item $tmp -Force
    $bb = [IO.File]::ReadAllBytes((Join-Path $base $rel))
    $same = ($rb.Length -eq $bb.Length)
    $firstDiff = -1
    if ($same) {
        for ($i = 0; $i -lt $rb.Length; $i++) {
            if ($rb[$i] -ne $bb[$i]) { $same = $false; $firstDiff = $i; break }
        }
    }
    Write-Output ($rel + '  realBytes=' + $rb.Length + '  baselineBytes=' + $bb.Length + '  identicalToOriginal=' + $same + '  firstDiff=' + $firstDiff)
}
Write-Output 'VERIFY-ROLLBACK-DONE'
