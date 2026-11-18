param(
    [string]$Root = 'd:\plain_view\66T\mis-t160-XH-ptz',
    [string]$Words = '稳相,稳像,增稳,防抖,抖动,稳定,补偿,陀螺,滤波'
)
$ErrorActionPreference = 'Stop'
$gbk = [Text.Encoding]::GetEncoding(936)
$kw = $Words.Split(',')
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
                if ($t.Length -gt 100) { $t = $t.Substring(0, 100) }
                Write-Output ($rel + ':' + ($i + 1) + ' | ' + $t)
                break
            }
        }
    }
}
Write-Output 'GREP-DONE'
