param(
    [Parameter(Mandatory = $true)][string]$PatchJson
)

# GBK 安全的批量替换 + 自动写 diffsnap 快照
# patch.json (UTF-8):
# {
#   "path": "D:\\plain_view\\...\\ptz.c",
#   "expectNonAscii": 30,
#   "snapshot": true,
#   "edits": [ { "old": "aaa", "new": "bbb" }, ... ]
# }

$ErrorActionPreference = 'Stop'
$json = [IO.File]::ReadAllText($PatchJson, (New-Object Text.UTF8Encoding($false)))
$patch = $json | ConvertFrom-Json
$path = $patch.path
$gbk = [Text.Encoding]::GetEncoding(936)

$raw = [IO.File]::ReadAllBytes($path)
$before = ($raw | Where-Object { $_ -gt 127 }).Count
$beforeLen = $raw.Length
$s = $gbk.GetString($raw).Replace("`r`n", "`n")

$i = 0
foreach ($e in $patch.edits) {
    $i++
    $old = ([string]$e.old).Replace("`r`n", "`n")
    $new = ([string]$e.new).Replace("`r`n", "`n")
    if ($s.IndexOf($old) -lt 0) { throw "anchor #$i not found" }
    $s = $s.Replace($old, $new)
    Write-Host ("edit #{0} applied" -f $i)
}

$s = $s.Replace("`n", "`r`n")
[IO.File]::WriteAllBytes($path, $gbk.GetBytes($s))

$b = [IO.File]::ReadAllBytes($path)
$after = ($b | Where-Object { $_ -gt 127 }).Count
$txt = $gbk.GetString($b)
$bad = ($txt.ToCharArray() | Where-Object { [int]$_ -eq 0xFFFD }).Count
Write-Host ("bytes {0} -> {1} | nonAscii {2} -> {3} | badChars {4}" -f $beforeLen, $b.Length, $before, $after, $bad)

if ($null -ne $patch.expectNonAscii -and [int]$patch.expectNonAscii -ne $after) {
    Write-Host ("WARN: nonAscii mismatch, expect {0} got {1}" -f $patch.expectNonAscii, $after)
}
if ($bad -gt 0) {
    throw "encoding damaged (bad chars present)"
}

if ($patch.snapshot -ne $false) {
    $env:ELECTRON_RUN_AS_NODE = '1'
    & 'D:\Vscode\Microsoft VS Code\Code.exe' 'D:\Codebuddy\tools\diffsnap-seed.js' $path
}
