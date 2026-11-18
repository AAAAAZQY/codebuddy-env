$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$gbk = [Text.Encoding]::GetEncoding(936)
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
foreach ($f in $files) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $s = $gbk.GetString($b)
    $lines = $s.Replace("`r`n", "`n").Split("`n")
    $hits = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Contains('[AI-COMMENT]')) { $hits += $i }
    }
    if ($hits.Count -eq 0) { continue }
    Write-Output ('===== ' + $f.FullName.Replace($root + '\', '') + ' hits=' + $hits.Count)
    # group consecutive
    $groups = @()
    $start = $hits[0]
    $prev = $hits[0]
    for ($k = 1; $k -lt $hits.Count; $k++) {
        if ($hits[$k] -ne $prev + 1) {
            $groups += ,@($start, $prev)
            $start = $hits[$k]
        }
        $prev = $hits[$k]
    }
    $groups += ,@($start, $prev)
    foreach ($g in $groups) {
        $a = $g[0]
        $z = $g[1]
        $prevLine = if ($a -gt 0) { $lines[$a - 1] } else { '<BOF>' }
        $nextLine = if ($z -lt $lines.Count - 1) { $lines[$z + 1] } else { '<EOF>' }
        Write-Output ('  block ' + ($a + 1) + '-' + ($z + 1) + ' (' + ($z - $a + 1) + ' lines)')
        Write-Output ('    prev[' + $a + ']: ' + $prevLine)
        Write-Output ('    next[' + ($z + 2) + ']: ' + $nextLine)
        for ($q = $a; $q -le $z; $q++) {
            $t = $lines[$q].Trim()
            if (-not $t.EndsWith('*/')) {
                Write-Output ('    NOT-CLOSED ' + ($q + 1) + ': ' + $t)
            }
            if (-not $t.StartsWith('/*')) {
                Write-Output ('    NOT-START ' + ($q + 1) + ': ' + $t)
            }
        }
    }
}
