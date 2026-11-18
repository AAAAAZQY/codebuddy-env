$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$gbk = [Text.Encoding]::GetEncoding(936)
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
$totalLines = 0
$totalFiles = 0
foreach ($f in $files) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $s = $gbk.GetString($b)
    $lines = $s.Replace("`r`n", "`n").Split("`n")
    $n = 0
    $mixed = 0
    $idx = 0
    foreach ($l in $lines) {
        $idx++
        if ($l.Contains('[AI-COMMENT]')) {
            $n++
            $t = $l.Trim()
            if (-not ($t.StartsWith('/*') -or $t.StartsWith('*') -or $t.StartsWith('//'))) {
                $mixed++
                Write-Output ("  MIXED " + $f.FullName.Replace($root + '\', '') + ":" + $idx + " => " + $t)
            }
        }
    }
    if ($n -gt 0) {
        $nonAscii = 0
        foreach ($by in $b) { if ($by -gt 127) { $nonAscii++ } }
        Write-Output ($f.FullName.Replace($root + '\', '') + '  aiLines=' + $n + '  mixed=' + $mixed + '  nonascii=' + $nonAscii + '  bytes=' + $b.Length)
        $totalLines += $n
        $totalFiles++
    }
}
Write-Output ('TOTAL_FILES=' + $totalFiles + '  TOTAL_LINES=' + $totalLines)
