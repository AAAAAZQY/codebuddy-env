# bridge-check.ps1 —— 校验副本与真实工程是否一致（filebridge 双向同步的安全网）
# 用法:
#   .\bridge-check.ps1                 只查 3 个关键文件
#   .\bridge-check.ps1 -Hours 2        查最近 2 小时内改动过的所有 .c/.h
#   .\bridge-check.ps1 -All            查整个工程
param(
    [switch]$All,
    [int]$Hours = 0,
    [string]$Mirror = 'd:\plain_view\66T\mis-t160-XH-ptz',
    [int]$Port = 37821
)

$ErrorActionPreference = 'Stop'
$meta = Get-Content (Join-Path $Mirror '.mirror-meta.json') -Raw | ConvertFrom-Json
$Real = $meta.real.TrimEnd('\')
Write-Host ("真实工程: " + $Real)
Write-Host ("副本    : " + $Mirror)
Write-Host ''

function Get-RealBytes([string]$absPath) {
    $u = 'http://127.0.0.1:' + $Port + '/read?p=' + [uri]::EscapeDataString($absPath)
    $j = (Invoke-WebRequest -Uri $u -TimeoutSec 10 -UseBasicParsing).Content | ConvertFrom-Json
    if (-not $j.ok) { throw ('桥返回失败: ' + $absPath) }
    return ,([Convert]::FromBase64String($j.data))
}

$files = @()
if ($All) {
    $files = Get-ChildItem $Mirror -Recurse -Include *.c,*.h -File |
             Where-Object { $_.FullName -notmatch '\\\.codebuddy\\' -and $_.FullName -notmatch '\\\.git\\' }
} elseif ($Hours -gt 0) {
    $files = Get-ChildItem $Mirror -Recurse -Include *.c,*.h -File |
             Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-$Hours) -and `
                            $_.FullName -notmatch '\\\.codebuddy\\' -and $_.FullName -notmatch '\\\.git\\' }
} else {
    $files = @('application\motor_bldc.c','application\inc\motor.h','bsw\pid.c') |
             ForEach-Object { Get-Item (Join-Path $Mirror $_) }
}

$bad = 0
$rows = @()
foreach ($f in $files) {
    $rel = $f.FullName.Substring($Mirror.Length + 1)
    $rp = Join-Path $Real $rel
    try {
        $rb = Get-RealBytes $rp
        $mb = [IO.File]::ReadAllBytes($f.FullName)
        $hr = [BitConverter]::ToString([Security.Cryptography.MD5]::Create().ComputeHash($rb)) -replace '-',''
        $hm = [BitConverter]::ToString([Security.Cryptography.MD5]::Create().ComputeHash($mb)) -replace '-',''
        $same = ($hr -eq $hm)
        if (-not $same) { $bad++ }
        $rows += [pscustomobject]@{
            文件 = $rel
            副本 = $mb.Length
            真实 = $rb.Length
            状态 = $(if ($same) { 'OK' } else { '不一致!' })
        }
    } catch {
        $bad++
        $rows += [pscustomobject]@{ 文件 = $rel; 副本 = $f.Length; 真实 = '-'; 状态 = ('读取失败: ' + $_.Exception.Message) }
    }
}

$rows | Format-Table -AutoSize

# 关键参数摘要（取真实工程，即 Keil 实际编译的内容）
try {
    $src = [Text.Encoding]::GetEncoding(936).GetString((Get-RealBytes (Join-Path $Real 'application\motor_bldc.c')))
    $lines = $src -split "`r?`n"
    foreach ($name in @('velocity_pid_pan','position_pid')) {
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match ('const PID_t ' + $name)) {
                Write-Host ("--- 真实工程 " + $name + " ---")
                for ($k = $i; $k -lt [Math]::Min($i + 12, $lines.Count); $k++) {
                    $t = $lines[$k].Trim()
                    if ($t -match '^\.(kp|ki|kd|integral_max|integral_min|output_max|output_min)') { Write-Host ('  ' + $t) }
                }
                break
            }
        }
    }
} catch {
    Write-Host ('参数摘要读取失败: ' + $_.Exception.Message)
}

Write-Host ''
if ($bad -eq 0) {
    Write-Host '结果: 全部一致，可以编译。' -ForegroundColor Green
    exit 0
} else {
    Write-Host ("结果: " + $bad + " 个文件不一致 —— 不要编译，先跑 bridge-pull.ps1 取回真实工程内容或重新保存副本。") -ForegroundColor Red
    exit 1
}
