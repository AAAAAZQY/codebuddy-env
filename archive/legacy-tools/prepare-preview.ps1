$ErrorActionPreference = 'Stop'

# ===== 只生成"拟改后"的预览副本 + 对照快照，真实工程与镜像目录都不动 =====
$enc = [Text.Encoding]::GetEncoding(28591)   # latin1, byte-safe
$mirror = 'D:\plain_view\66T\mis-t160-main-ptz'
$preview = 'D:\Codebuddy\tmp\preview'
$nl = "`r`n"

if (Test-Path $preview) { Remove-Item $preview -Recurse -Force }
New-Item -ItemType Directory -Path $preview -Force | Out-Null

$files = @('application\inc\cfg_mcu.h', 'application\cfg_mcu.c')
foreach ($rel in $files) {
    $dst = Join-Path $preview $rel
    $dir = Split-Path $dst -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item (Join-Path $mirror $rel) $dst -Force
}

# --- 1) cfg_mcu.h : IMU 换到 UART8 ---
$h = Join-Path $preview 'application\inc\cfg_mcu.h'
$hb = [IO.File]::ReadAllBytes($h)
$hs = $enc.GetString($hb)
$oldH = '#define IMU_UART_CH                 UART_CH_7'
$newH = '#define IMU_UART_CH                 UART_CH_8'
if ($hs.IndexOf($oldH) -lt 0) { Write-Output 'ABORT cfg_mcu.h anchor'; exit 1 }
$hs = $hs.Replace($oldH, $newH)
[IO.File]::WriteAllBytes($h, $enc.GetBytes($hs))
Write-Output ('cfg_mcu.h  ' + $hb.Length + ' -> ' + ([IO.File]::ReadAllBytes($h)).Length)

# --- 2) cfg_mcu.c : debug 不初始化（结构保留） ---
$c = Join-Path $preview 'application\cfg_mcu.c'
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
if ($cs.IndexOf($oldC) -lt 0) { Write-Output 'ABORT cfg_mcu.c anchor'; exit 1 }
$cs = $cs.Replace($oldC, $newC)
[IO.File]::WriteAllBytes($c, $enc.GetBytes($cs))
Write-Output ('cfg_mcu.c  ' + $cb.Length + ' -> ' + ([IO.File]::ReadAllBytes($c)).Length)

# --- 3) 生成对照快照：快照=镜像现状（改前），索引文件=预览文件（改后） ---
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

function Md5Hex12([string]$text) {
    $md5 = [Security.Cryptography.MD5]::Create()
    $b = $md5.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))
    $sb = ''
    foreach ($x in $b) { $sb += $x.ToString('x2') }
    return $sb.Substring(0, 12)
}

foreach ($rel in $files) {
    $beforePath = Join-Path $mirror $rel
    $afterPath = Join-Path $preview $rel
    $key = $afterPath.ToLower()
    $dir = Join-Path $snapsRoot (Md5Hex12 $key)
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $ts = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
    $snapPath = Join-Path $dir ($ts.ToString() + '-' + [IO.Path]::GetFileName($afterPath))
    [IO.File]::WriteAllBytes($snapPath, [IO.File]::ReadAllBytes($beforePath))
    $snaps = @()
    if ($index.ContainsKey($key) -and $index[$key].snaps) { $snaps = @($index[$key].snaps) }
    $snaps += [pscustomobject]@{ ts = $ts; path = $snapPath }
    $index[$key] = [pscustomobject]@{
        fsPath = $afterPath
        name   = [IO.Path]::GetFileName($afterPath)
        snaps  = $snaps
    }
    Write-Output ('snapshot ready: ' + [IO.Path]::GetFileName($afterPath) + '  (left=mirror now, right=preview)')
}

$index | ConvertTo-Json -Depth 8 | Set-Content -Path $indexPath -Encoding UTF8
Write-Output ('INDEX-ENTRIES=' + $index.Keys.Count)
Write-Output 'PREPARE-PREVIEW-DONE'
