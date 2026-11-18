# bridge-pull.ps1 —— 从真实工程把内容拉回副本（真实为准，把副本追平）
# 用法:
#   .\bridge-pull.ps1 -File application\motor_bldc.c [-FromBackup]
#   .\bridge-pull.ps1 -Changed                 列出所有不一致的 .c/.h 并拉回（默认先备份）
#   .\bridge-pull.ps1 -Changed -DryRun         只比对列表，不写文件
#   .\bridge-pull.ps1 -Changed -Force          连“副本较新”的也一起用真实覆盖
#   .\bridge-pull.ps1 -Changed -NoBackup       不备份直接写
#   .\bridge-pull.ps1 -Changed -Mirror D:\plain_view\S100\s100-XA-source_code_ptz
# 说明: 只写副本，绝不写真实工程；真实内容一律经桥接 /read 取明文。
param(
    [string]$File,
    [switch]$FromBackup,
    [switch]$Changed,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$NoBackup,
    [string]$Mirror = 'd:\plain_view\66T\mis-t160-XH-ptz',
    [int]$Port = 37821
)

$ErrorActionPreference = 'Stop'

if (-not $Changed -and -not $File) {
    Write-Host '用法: -File <相对路径> 单文件拉回，或 -Changed 批量比对拉回'
    exit 2
}

$meta = Get-Content (Join-Path $Mirror '.mirror-meta.json') -Raw | ConvertFrom-Json
$Real = $meta.real.TrimEnd('\')

function Get-RealBytes([string]$absPath) {
    $u = 'http://127.0.0.1:' + $Port + '/read?p=' + [uri]::EscapeDataString($absPath)
    $j = (Invoke-WebRequest -Uri $u -TimeoutSec 20 -UseBasicParsing).Content | ConvertFrom-Json
    if (-not $j.ok) { throw ('桥读取失败: ' + $absPath) }
    return , ([Convert]::FromBase64String($j.data))
}

function Get-Md5([byte[]]$bytes) {
    return ([BitConverter]::ToString([Security.Cryptography.MD5]::Create().ComputeHash($bytes)) -replace '-', '')
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$bakDir = Join-Path $Mirror '.codebuddy'
$bakSub = Join-Path $bakDir ('rescue-' + $stamp)

function Save-Backup([string]$rel) {
    if ($NoBackup) { return }
    if (-not (Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir | Out-Null }
    $dst = Join-Path $bakSub $rel
    $d = Split-Path $dst -Parent
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    Copy-Item (Join-Path $Mirror $rel) $dst -Force
}

function Write-MirrorFile([string]$rel, [byte[]]$bytes) {
    $mp = Join-Path $Mirror $rel
    $d = Split-Path $mp -Parent
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    [IO.File]::WriteAllBytes($mp, $bytes)
    return (Get-Md5 ([IO.File]::ReadAllBytes($mp)))
}

# ---------------- 单文件模式 ----------------
if ($File) {
    $mp = Join-Path $Mirror $File
    $rp = Join-Path $Real   $File
    if ($FromBackup -and (Test-Path $mp)) {
        if (-not (Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir | Out-Null }
        $bak = Join-Path $bakDir ('rescue-' + $stamp + '-' + (Split-Path $File -Leaf))
        Copy-Item $mp $bak -Force
        Write-Host ('副本已备份到: ' + $bak)
    }
    $bytes = Get-RealBytes $rp
    if ($DryRun) {
        Write-Host ('[DryRun] 真实 ' + $bytes.Length + ' 字节，未写入副本: ' + $File)
        exit 0
    }
    $hm = Write-MirrorFile $File $bytes
    $hr = Get-Md5 $bytes
    Write-Host ('已从真实工程拉回: ' + $File)
    Write-Host ('  写入字节 = ' + $bytes.Length)
    Write-Host ('  校验: ' + $(if ($hm -eq $hr) { 'MD5 一致 OK' } else { 'MD5 不一致!' }))
    Write-Host '  注意: 若 VSCode 里该文件仍处于编辑状态, 请关闭标签页重新打开, 否则保存会用旧缓冲区覆盖。'
    exit 0
}

# ---------------- 批量模式 ---------------- 全部 c/h 逐一比对 ----------------
Write-Host ('真实工程: ' + $Real)
Write-Host ('副本    : ' + $Mirror)
Write-Host ('备份目录: ' + $(if ($NoBackup) { '(不备份)' } else { $bakSub }))
Write-Host ''

$files = Get-ChildItem $Mirror -Recurse -Include *.c,*.h -File |
         Where-Object { $_.FullName -notmatch '\\\.codebuddy\\' -and $_.FullName -notmatch '\\\.git\\' }

$rows = @()
$pulled = 0
$newer = 0
$missing = 0
$same = 0
$failed = 0

foreach ($f in $files) {
    $rel = $f.FullName.Substring($Mirror.Length + 1)
    $rp = Join-Path $Real $rel
    $mb = [IO.File]::ReadAllBytes($f.FullName)
    $hm = Get-Md5 $mb

    try {
        $rb = Get-RealBytes $rp
    } catch {
        $missing++
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $mb.Length; 真实 = '-'; 结论 = '真实缺失/读取失败'; 动作 = '跳过' }
        continue
    }

    $hr = Get-Md5 $rb
    if ($hr -eq $hm) { $same++; continue }

    $rt = (Get-Item $rp).LastWriteTime
    $mt = $f.LastWriteTime
    $realNewer = ($rt -gt $mt.AddSeconds(1))

    if (-not $realNewer -and -not $Force) {
        $newer++
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $mb.Length; 真实 = $rb.Length; 结论 = ('内容不同，副本较新(真实 ' + $rt.ToString('HH:mm:ss') + ' / 副本 ' + $mt.ToString('HH:mm:ss') + ')'); 动作 = '跳过(需推送)' }
        continue
    }

    if ($DryRun) {
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $mb.Length; 真实 = $rb.Length; 结论 = '内容不同，真实较新'; 动作 = '[DryRun] 未写' }
        continue
    }

    try {
        Save-Backup $rel
        $w = Write-MirrorFile $rel $rb
        if ($w -ne $hr) { throw '写后 MD5 不一致' }
        $pulled++
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $mb.Length; 真实 = $rb.Length; 结论 = '内容不同，真实较新'; 动作 = '已拉回' }
    } catch {
        $failed++
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $mb.Length; 真实 = $rb.Length; 结论 = '内容不同'; 动作 = ('写入失败: ' + $_.Exception.Message) }
    }
}

if ($rows.Count) { $rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host }
else { Write-Host '没有不一致的文件。' }

Write-Host ''
Write-Host ("合计: 检查 {0} 个, 一致 {1}, 已拉回 {2}, 副本较新跳过 {3}, 真实缺失 {4}, 失败 {5}" -f $files.Count, $same, $pulled, $newer, $missing, $failed)
if ($pulled -gt 0) {
    Write-Host ('备份: ' + $bakSub)
    Write-Host '若 VSCode 里相关文件还开着，请关闭重开，否则保存会用旧缓冲区覆盖拉回的内容。'
}
if ($newer -gt 0) {
    Write-Host '有文件副本较新（未覆盖）：确认要以真实为准再跑 -Force，或在副本里重新保存让桥接推送到真实。'
}
if ($failed -gt 0) { exit 1 }
exit 0
