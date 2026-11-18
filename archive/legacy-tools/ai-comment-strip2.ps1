$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$backupRoot = 'D:\Codebuddy\backup\ai-comment-20261020'
$markerBytes = [byte[]](0x5B,0x41,0x49,0x2D,0x43,0x4F,0x4D,0x4D,0x45,0x4E,0x54,0x5D)
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
$changed = 0
foreach ($f in $files) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $rel = $f.FullName.Substring($root.Length).TrimStart('\')

    # find all marker offsets
    $hits = New-Object System.Collections.Generic.List[int]
    for ($i = 0; $i -le $b.Length - $markerBytes.Length; $i++) {
        if ($b[$i] -eq $markerBytes[0]) {
            $ok = $true
            for ($j = 1; $j -lt $markerBytes.Length; $j++) {
                if ($b[$i + $j] -ne $markerBytes[$j]) { $ok = $false; break }
            }
            if ($ok) { $hits.Add($i) }
        }
    }
    if ($hits.Count -eq 0) { continue }

    # compute line ranges
    $starts = New-Object System.Collections.Generic.List[int]
    $ends = New-Object System.Collections.Generic.List[int]
    $skipped = 0
    foreach ($p in $hits) {
        $s = 0
        $k = $p - 1
        while ($k -ge 0) {
            if ($b[$k] -eq 0x0A) { $s = $k + 1; break }
            $k--
        }
        $e = $b.Length
        $k = $p
        while ($k -lt $b.Length) {
            if ($b[$k] -eq 0x0A) { $e = $k + 1; break }
            $k++
        }
        # leading non-space bytes of the line
        $q = $s
        while ($q -lt $e -and ($b[$q] -eq 0x20 -or $b[$q] -eq 0x09)) { $q++ }
        $isComment = ($q + 2 -le $b.Length) -and ($b[$q] -eq 0x2F) -and ($b[$q + 1] -eq 0x2A)
        if (-not $isComment) { $skipped++; continue }
        [void]$starts.Add($s)
        [void]$ends.Add($e)
    }

    # merge ranges
    $ms = New-Object System.Collections.Generic.List[int]
    $me = New-Object System.Collections.Generic.List[int]
    for ($i = 0; $i -lt $starts.Count; $i++) {
        if ($ms.Count -gt 0 -and $starts[$i] -le $me[$me.Count - 1]) {
            if ($ends[$i] -gt $me[$me.Count - 1]) { $me[$me.Count - 1] = $ends[$i] }
        } else {
            [void]$ms.Add($starts[$i])
            [void]$me.Add($ends[$i])
        }
    }

    $removedLen = 0
    for ($i = 0; $i -lt $ms.Count; $i++) { $removedLen += ($me[$i] - $ms[$i]) }
    $out = New-Object System.Collections.Generic.List[byte]
    $pos = 0
    for ($i = 0; $i -lt $ms.Count; $i++) {
        for ($k = $pos; $k -lt $ms[$i]; $k++) { [void]$out.Add($b[$k]) }
        $pos = $me[$i]
    }
    for ($k = $pos; $k -lt $b.Length; $k++) { [void]$out.Add($b[$k]) }
    $newBytes = $out.ToArray()
    if (($b.Length - $newBytes.Length) -ne $removedLen) {
        Write-Output ('ABORT length check failed in ' + $rel)
        continue
    }

    # backup then write
    $bak = Join-Path $backupRoot $rel
    $bakDir = Split-Path $bak -Parent
    if (-not (Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir -Force | Out-Null }
    [IO.File]::WriteAllBytes($bak, $b)
    [IO.File]::WriteAllBytes($f.FullName, $newBytes)
    $changed++
    Write-Output ('OK ' + $rel + '  linesRemoved=' + $ms.Count + '  skipped=' + $skipped + '  bytes ' + $b.Length + ' -> ' + $newBytes.Length)
}
Write-Output ('FILES_CHANGED=' + $changed)
