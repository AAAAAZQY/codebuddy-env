$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:37821'
$mirror = 'D:\plain_view\22b2\22b2-SST-ptz\application\inc\led.h'
$real = 'd:\aMyProject\Project\22b2\SST\22b2\ptz_source_code\source_code\application\inc\led.h'
$tmp = 'C:\Users\myages2026\AppData\Local\Temp\drill_'

function GetRawBytes([string]$p, [string]$out) {
    Invoke-WebRequest -UseBasicParsing -Uri ($base + '/raw?p=' + [uri]::EscapeDataString($p)) -OutFile $out
    return ,([IO.File]::ReadAllBytes($out))
}
function PutReal([string]$p, [byte[]]$bytes) {
    $b64 = [Convert]::ToBase64String($bytes)
    Invoke-WebRequest -UseBasicParsing -Method Post -Uri ($base + '/write?p=' + [uri]::EscapeDataString($p)) -Body $b64 -ContentType 'text/plain' | Out-Null
}
function PutMirrorPlain([string]$p, [byte[]]$bytes) {
    $t = $p + '.~brgtmp'
    [IO.File]::WriteAllBytes($t, $bytes)
    $ok = $false
    for ($k = 0; $k -lt 5 -and -not $ok; $k++) {
        try {
            if (Test-Path $p) { [IO.File]::Replace($t, $p, [NullString]::Value) } else { [IO.File]::Move($t, $p) }
            $ok = $true
        } catch { Start-Sleep -Milliseconds 60 }
    }
    if (-not $ok) { [IO.File]::WriteAllBytes($p, $bytes); Remove-Item $t -Force -ErrorAction SilentlyContinue }
}
function Same([byte[]]$a, [byte[]]$b) { return ([Convert]::ToBase64String($a) -eq [Convert]::ToBase64String($b)) }

$origReal = GetRawBytes $real ($tmp + 'r0')
$origMirror = GetRawBytes $mirror ($tmp + 'm0')
Write-Host ('[0] baseline real=' + $origReal.Length + ' mirror=' + $origMirror.Length + ' equal=' + (Same $origReal $origMirror))

Write-Host '[1] /write to a mirror path must be refused:'
try {
    PutReal $mirror ([Text.Encoding]::ASCII.GetBytes('x'))
    Write-Host '  FAIL: accepted'
} catch {
    $code = '?'
    try { $code = [int]$_.Exception.Response.StatusCode } catch { }
    Write-Host ('  status=' + $code + ' (expect 403)')
}

$newA = [byte[]]($origReal + [Text.Encoding]::ASCII.GetBytes("`r`n/* drill mirror->real */`r`n"))
PutMirrorPlain $mirror $newA
Start-Sleep -Seconds 3
$r = GetRawBytes $real ($tmp + 'rA')
$m = GetRawBytes $mirror ($tmp + 'mA')
Write-Host ('[2] mirror->real: real match=' + (Same $r $newA) + ' mirror kept=' + (Same $m $newA))

$newB = [byte[]]($origReal + [Text.Encoding]::ASCII.GetBytes("`r`n/* drill real->mirror */`r`n"))
PutReal $real $newB
Start-Sleep -Seconds 3
$m2 = GetRawBytes $mirror ($tmp + 'mB')
$r2 = GetRawBytes $real ($tmp + 'rB')
Write-Host ('[3] real->mirror: mirror match=' + (Same $m2 $newB) + ' real kept=' + (Same $r2 $newB))

PutReal $real $origReal
Start-Sleep -Milliseconds 1500
PutMirrorPlain $mirror $origReal
Start-Sleep -Seconds 3
$r3 = GetRawBytes $real ($tmp + 'rC')
$m3 = GetRawBytes $mirror ($tmp + 'mC')
$mm = (Get-Item $mirror).Length
Write-Host ('[4] restored: real=' + (Same $r3 $origReal) + ' mirror=' + (Same $m3 $origReal) + ' mirrorSize=' + $mm + ' dlpAligned=' + (($mm % 8192) -eq 0))

Remove-Item ($tmp + 'r0'), ($tmp + 'm0'), ($tmp + 'rA'), ($tmp + 'mA'), ($tmp + 'mB'), ($tmp + 'rB'), ($tmp + 'rC'), ($tmp + 'mC') -Force -ErrorAction SilentlyContinue
Write-Host '--- log ---'
Write-Host (Invoke-WebRequest -UseBasicParsing -Uri ($base + '/log?n=14')).Content
