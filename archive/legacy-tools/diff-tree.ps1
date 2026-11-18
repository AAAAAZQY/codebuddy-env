$ErrorActionPreference = 'Stop'
$a = 'd:\plain_view\66T\mis-t160-XH-ptz'
$b = 'D:\plain_view\mis-t160-main-ptz'
function RelList($root) {
    $set = @{}
    Get-ChildItem -Path $root -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\')
        if ($rel.StartsWith('.vscode') -or $rel.StartsWith('.mirror')) { return }
        $set[$rel] = $_.Length
    }
    return $set
}
$la = RelList $a
$lb = RelList $b
Write-Output '--- only in 66T (XH) ---'
$la.Keys | Sort-Object | ForEach-Object { if (-not $lb.ContainsKey($_)) { Write-Output ('  ' + $_ + '  ' + $la[$_]) } }
Write-Output '--- only in new/mis-t160 (main) ---'
$lb.Keys | Sort-Object | ForEach-Object { if (-not $la.ContainsKey($_)) { Write-Output ('  ' + $_ + '  ' + $lb[$_]) } }
Write-Output '--- size differs (application,bsw,hal) ---'
$la.Keys | Sort-Object | ForEach-Object {
    if ($lb.ContainsKey($_) -and $la[$_] -ne $lb[$_]) {
        if ($_ -like 'application*' -or $_ -like 'bsw*' -or $_ -like 'hal*') {
            Write-Output ('  ' + $_ + '  66T=' + $la[$_] + '  main=' + $lb[$_])
        }
    }
}
Write-Output 'TREE-DONE'
