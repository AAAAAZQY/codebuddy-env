$ErrorActionPreference = 'Stop'
$base = 'D:\Codebuddy\tmp\main'          # 改动前的原始明文
$real = 'D:\aMyProject\Project\MIS-T160\mian\new\mis-t160\ptz_source_code\source_code'
$mirror66t = 'D:\plain_view\66T\mis-t160-main-ptz'
$mirrorTop = 'D:\plain_view\mis-t160-main-ptz'
$files = @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')
$enc = [Text.Encoding]::GetEncoding(28591)

Write-Output '=== 1) restore real project ==='
foreach ($rel in $files) {
    $bb = [IO.File]::ReadAllBytes((Join-Path $base $rel))
    $b64 = [Convert]::ToBase64String($bb)
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/write?p=' + [uri]::EscapeDataString($rp)
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Body $b64 -Uri $u
    Write-Output ('real  ' + $rel + '  ' + $resp.Content)
}

Write-Output '=== 2) restore mirrors (plain text, written by untrusted process) ==='
foreach ($m in @($mirror66t, $mirrorTop)) {
    if (-not (Test-Path $m)) { Write-Output ('skip missing mirror: ' + $m); continue }
    foreach ($rel in $files) {
        $bb = [IO.File]::ReadAllBytes((Join-Path $base $rel))
        $dst = Join-Path $m $rel
        if (-not (Test-Path $dst)) { Write-Output ('  skip ' + $m + ' :: ' + $rel); continue }
        [IO.File]::WriteAllBytes($dst, $bb)
        Write-Output ('  restored ' + $m + ' :: ' + $rel + '  bytes=' + $bb.Length)
    }
}

Write-Output '=== 3) clean diff-snap entries for these files ==='
$indexPath = Join-Path $env:APPDATA 'CodeBuddy CN\User\globalStorage\local.diff-snap\snaps\index.json'
if (Test-Path $indexPath) {
    $raw = Get-Content $indexPath -Raw -Encoding UTF8
    $obj = $raw | ConvertFrom-Json
    $keep = [ordered]@{}
    foreach ($p in $obj.PSObject.Properties) {
        $path = [string]$p.Value.fsPath
        if ($path -like '*mis-t160-main-ptz*' -or $path -like '*Codebuddy\tmp\main*' -or $path -like '*Codebuddy\tmp\preview*') {
            Write-Output ('  drop index entry: ' + $path)
            continue
        }
        $keep[$p.Name] = $p.Value
    }
    ($keep | ConvertTo-Json -Depth 8) | Set-Content -Path $indexPath -Encoding UTF8
    Write-Output ('  remaining entries: ' + $keep.Keys.Count)
}

Write-Output '=== 4) verify ==='
foreach ($rel in $files) {
    $bb = [IO.File]::ReadAllBytes((Join-Path $base $rel))
    $rp = Join-Path $real $rel
    $u = 'http://127.0.0.1:37821/raw?p=' + [uri]::EscapeDataString($rp)
    $tmp = [IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $u
    $rb = [IO.File]::ReadAllBytes($tmp)
    Remove-Item $tmp -Force
    $realSame = ($rb.Length -eq $bb.Length)
    if ($realSame) { for ($i = 0; $i -lt $bb.Length; $i++) { if ($rb[$i] -ne $bb[$i]) { $realSame = $false; break } } }
    Write-Output ('real  ' + $rel + '  bytes=' + $rb.Length + '  backToOriginal=' + $realSame)
    foreach ($m in @($mirror66t, $mirrorTop)) {
        if (-not (Test-Path $m)) { continue }
        $mp = Join-Path $m $rel
        if (-not (Test-Path $mp)) { continue }
        $mb = [IO.File]::ReadAllBytes($mp)
        $ms = ($mb.Length -eq $bb.Length)
        if ($ms) { for ($i = 0; $i -lt $bb.Length; $i++) { if ($mb[$i] -ne $bb[$i]) { $ms = $false; break } } }
        Write-Output ('  ' + $m + '  bytes=' + $mb.Length + '  backToOriginal=' + $ms)
    }
}
Write-Output 'ROLLBACK-ALL-DONE'
