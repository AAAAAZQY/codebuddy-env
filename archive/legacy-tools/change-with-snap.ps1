$ErrorActionPreference = 'Stop'

# ===== 在副本里改文件，并在改之前把原内容存成 diff-snap 快照 =====
# 这样在 CodeBuddy 的「改动对比」里点开，就是该工程文件的 改动前 vs 改动后 并排 diff。
$enc = [Text.Encoding]::GetEncoding(28591)   # latin1, byte-safe
$nl = "`r`n"
$mirror = 'D:\plain_view\66T\mis-t160-main-ptz'
$files = @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')

$snapsRoot = Join-Path $env:APPDATA 'CodeBuddy CN\User\globalStorage\local.diff-snap\snaps'
$indexPath = Join-Path $snapsRoot 'index.json'
$index = @{}
if (Test-Path $indexPath) {
    $raw = Get-Content $indexPath -Raw -Encoding UTF8
    if ($raw.Trim().Length -gt 0) {
        $obj = $raw | ConvertFrom-Json
        foreach ($p in $obj.PSObject.Properties) { $index[$p.Name] = $p.Value }
    }
}

# 清掉上一轮指向 tmp\preview 的条目（那是绕路方案，不再使用）
$drop = @()
foreach ($k in $index.Keys) { if ($k -like '*codebuddy\tmp\preview*') { $drop += $k } }
foreach ($k in $drop) { Write-Output ('drop preview entry: ' + $index[$k].fsPath); $index.Remove($k) }

function Md5Hex12([string]$text) {
    $md5 = [Security.Cryptography.MD5]::Create()
    $b = $md5.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))
    $sb = ''
    foreach ($x in $b) { $sb += $x.ToString('x2') }
    return $sb.Substring(0, 12)
}

# 1) 先为每个文件存"改动前"快照
foreach ($rel in $files) {
    $p = Join-Path $mirror $rel
    if (-not (Test-Path $p)) { Write-Output ('ABORT missing ' + $p); exit 1 }
    $key = $p.ToLower()
    $dir = Join-Path $snapsRoot (Md5Hex12 $key)
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $ts = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
    $snapPath = Join-Path $dir ($ts.ToString() + '-' + [IO.Path]::GetFileName($p))
    [IO.File]::WriteAllBytes($snapPath, [IO.File]::ReadAllBytes($p))
    $snaps = @()
    if ($index.ContainsKey($key) -and $index[$key].snaps) { $snaps = @($index[$key].snaps) }
    $snaps += [pscustomobject]@{ ts = $ts; path = $snapPath }
    $index[$key] = [pscustomobject]@{
        fsPath = $p
        name   = [IO.Path]::GetFileName($p)
        snaps  = $snaps
    }
    Write-Output ('before-snapshot: ' + $rel + ' -> ' + $snapPath)
}
$index | ConvertTo-Json -Depth 8 | Set-Content -Path $indexPath -Encoding UTF8

# 2) 改副本（= 改真实工程，扩展会自动同步）
$h = Join-Path $mirror 'application\inc\cfg_mcu.h'
$hb = [IO.File]::ReadAllBytes($h)
$hs = $enc.GetString($hb)
$oldH = '#define IMU_UART_CH                 UART_CH_7'
$newH = '#define IMU_UART_CH                 UART_CH_8'
if ($hs.IndexOf($oldH) -lt 0) { Write-Output 'ABORT cfg_mcu.h anchor not found'; exit 1 }
$hs = $hs.Replace($oldH, $newH)
[IO.File]::WriteAllBytes($h, $enc.GetBytes($hs))
$ha = [IO.File]::ReadAllBytes($h)
Write-Output ('cfg_mcu.h  ' + $hb.Length + ' -> ' + $ha.Length)

$c = Join-Path $mirror 'application\cfg_mcu.c'
$cb = [IO.File]::ReadAllBytes($c)
$cs = $enc.GetString($cb)
$oldC = (@(
    '    uart_init(&g_uart_cfg[5]);',
    '    g_uart_debug = uart_get_serial(g_uart_cfg[5].ch);'
) -join $nl)
$newC = (@(
    '    /* debug uart disabled on purpose: config entry and handle are kept, port is not initialised */',
    '    //uart_init(&g_uart_cfg[5]);',
    '    //g_uart_debug = uart_get_serial(g_uart_cfg[5].ch);'
) -join $nl)
if ($cs.IndexOf($oldC) -lt 0) { Write-Output 'ABORT cfg_mcu.c anchor not found'; exit 1 }
$cs = $cs.Replace($oldC, $newC)
[IO.File]::WriteAllBytes($c, $enc.GetBytes($cs))
$ca = [IO.File]::ReadAllBytes($c)
Write-Output ('cfg_mcu.c  ' + $cb.Length + ' -> ' + $ca.Length)
Write-Output 'CHANGE-DONE'
