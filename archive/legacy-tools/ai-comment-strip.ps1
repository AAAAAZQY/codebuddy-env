$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$gbk = [Text.Encoding]::GetEncoding(936)
$backupRoot = 'D:\Codebuddy\backup\ai-comment-20261020'
$marker = '[AI-COMMENT]'
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
$changed = 0
foreach ($f in $files) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $s = $gbk.GetString($b)
    if (-not $s.Contains($marker)) { continue }

    # newline sanity: only CRLF allowed
    $loneLF = 0
    for ($i = 0; $i -lt $s.Length; $i++) {
        if ($s[$i] -eq [char]10 -and ($i -eq 0 -or $s[$i - 1] -ne [char]13)) { $loneLF++ }
    }
    if ($loneLF -gt 0) {
        Write-Output ('ABORT lone-LF=' + $loneLF + ' in ' + $f.FullName)
        continue
    }

    $lines = $s.Replace("`r`n", "`n").Split("`n")
    $kept = New-Object System.Collections.Generic.List[string]
    $removed = New-Object System.Collections.Generic.List[string]
    foreach ($l in $lines) {
        if ($l.Contains($marker)) { $removed.Add($l) } else { $kept.Add($l) }
    }
    if ($removed.Count -eq 0) { continue }

    # backup
    $rel = $f.FullName.Substring($root.Length).TrimStart('\')
    $bak = Join-Path $backupRoot $rel
    $bakDir = Split-Path $bak -Parent
    if (-not (Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir -Force | Out-Null }
    [IO.File]::WriteAllBytes($bak, $b)

    $newText = ($kept -join "`n").Replace("`n", "`r`n")
    if ($newText.Contains($marker)) { Write-Output ('ABORT marker survived in ' + $rel); continue }

    $removedText = ($removed -join "`r`n")
    if ($s.EndsWith("`r`n")) { $removedText = $removedText + "`r`n" }
    $expectDelta = $gbk.GetByteCount($removedText)
    $newBytes = $gbk.GetBytes($newText)
    $delta = $b.Length - $newBytes.Length

    if ($delta -ne $expectDelta) {
        Write-Output ('ABORT delta mismatch in ' + $rel + ' delta=' + $delta + ' expect=' + $expectDelta)
        continue
    }

    [IO.File]::WriteAllBytes($f.FullName, $newBytes)
    $changed++
    Write-Output ('OK ' + $rel + '  removedLines=' + $removed.Count + '  bytes ' + $b.Length + ' -> ' + $newBytes.Length + ' (delta=' + $delta + ')')
}
Write-Output ('FILES_CHANGED=' + $changed)
