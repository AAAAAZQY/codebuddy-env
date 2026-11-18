$ErrorActionPreference = 'Stop'
$p = 'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN\User\globalStorage\state.vscdb'
$fs = New-Object IO.FileStream($p, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
$bytes = New-Object byte[] $fs.Length
$read = 0
while ($read -lt $bytes.Length) {
    $n = $fs.Read($bytes, $read, $bytes.Length - $read)
    if ($n -le 0) { break }
    $read += $n
}
$fs.Close()
$txt = [Text.Encoding]::UTF8.GetString($bytes)
$kwFile = [string]([char]0x786C + [char]0x4EF6)      # ying jian
$kwStab = [string]([char]0x7A33 + [char]0x50CF)      # wen xiang
$kwImg = [string]([char]0x7A33 + [char]0x76F8)       # wen xiang alt
$kw = @($kwFile, $kwStab, $kwImg, 'UART7', 'IMU5146', 'imu5146')
$seen = 0
foreach ($w in $kw) {
    $idx = 0
    $count = 0
    while ($true) {
        $i = $txt.IndexOf($w, $idx, [StringComparison]::Ordinal)
        if ($i -lt 0) { break }
        $count++
        $idx = $i + $w.Length
        if ($count -gt 6) { continue }
        $st = [Math]::Max(0, $i - 220)
        $len = [Math]::Min(460, $txt.Length - $st)
        $frag = $txt.Substring($st, $len)
        $frag = $frag -replace "[^\u0020-\u007E\u4e00-\u9fff]", ' '
        $frag = $frag -replace '\s+', ' '
        Write-Output ('=== [' + $w + '] hit ' + $count + ' ===')
        Write-Output $frag
        $seen++
        if ($seen -gt 18) { break }
    }
}
Write-Output ('PEEK-DONE hits=' + $seen)
