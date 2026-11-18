$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$backupRoot = 'D:\Codebuddy\backup\ai-comment-20261020'
$gbk = [Text.Encoding]::GetEncoding(936)
$marker = '[AI-COMMENT]'
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
foreach ($f in $files) {
    $bak = Join-Path $backupRoot $f.FullName.Substring($root.Length).TrimStart('\')
    if (-not (Test-Path $bak)) { continue }
    $rel = $f.FullName.Substring($root.Length).TrimStart('\')
    $oldB = [IO.File]::ReadAllBytes($bak)
    $newB = [IO.File]::ReadAllBytes($f.FullName)
    $oldS = $gbk.GetString($oldB)
    $newS = $gbk.GetString($newB)

    # 1 marker gone
    $mk = 0
    for ($i = 0; $i -le $newB.Length - 12; $i++) { if ($newB[$i] -eq 0x5B -and $newB[$i + 1] -eq 0x41) { $mk++ } }
    $hasMarker = $newS.Contains($marker)

    # 2 compare line-filtered old with new
    $oldLines = $oldS.Split("`n")
    $kept = @()
    $dropped = 0
    foreach ($l in $oldLines) {
        if ($l.Contains($marker)) { $dropped++ } else { $kept += $l }
    }
    $expect = ($kept -join "`n")
    $same = ($expect -ceq $newS)

    # 3 comment delimiters balanced
    $open = ([regex]::Matches($newS, '/\*')).Count
    $close = ([regex]::Matches($newS, '\*/')).Count
    $bo = ([regex]::Matches($newS, '\{')).Count
    $bc = ([regex]::Matches($newS, '\}')).Count

    Write-Output ($rel + '  markerLeft=' + $hasMarker + '  droppedLines=' + $dropped + '  filteredMatch=' + $same + '  commentOpen=' + $open + ' close=' + $close + '  brace ' + $bo + '/' + $bc)
}
Write-Output 'VERIFY-DONE'
