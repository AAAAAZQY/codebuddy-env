param(
    [string]$Root = 'd:\plain_view\66T\mis-t160-XH-ptz'
)
$ErrorActionPreference = 'Stop'
$gbk = [Text.Encoding]::GetEncoding(936)
# keywords built from code points so this script stays pure ASCII
$kw = @()
$kw += [string]([char]0x7A33 + [char]0x76F8)          # wen xiang (stabilize image)
$kw += [string]([char]0x7A33 + [char]0x50CF)          # wen xiang variant
$kw += [string]([char]0x589E + [char]0x7A33)          # zeng wen
$kw += [string]([char]0x9632 + [char]0x6296)          # fang dou
$kw += [string]([char]0x6296 + [char]0x52A8)          # dou dong
$kw += [string]([char]0x7A33 + [char]0x5B9A)          # wen ding
$kw += [string]([char]0x8865 + [char]0x507F)          # bu chang
$kw += [string]([char]0x9640 + [char]0x87BA)          # tuo luo
$kw += [string]([char]0x6EE4 + [char]0x6CE2)          # lv bo
$files = Get-ChildItem -Path $Root -Recurse -Include *.c,*.h -File
foreach ($f in $files) {
    $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
    if ($rel -like 'third_party*') { continue }
    $s = $gbk.GetString([IO.File]::ReadAllBytes($f.FullName))
    $lines = $s.Replace("`r`n", "`n").Split("`n")
    for ($i = 0; $i -lt $lines.Count; $i++) {
        foreach ($w in $kw) {
            if ($lines[$i].Contains($w)) {
                $t = $lines[$i].Trim()
                if ($t.Length -gt 110) { $t = $t.Substring(0, 110) }
                Write-Output ($rel + ':' + ($i + 1) + ' | ' + $t)
                break
            }
        }
    }
}
Write-Output 'GREP-DONE'
