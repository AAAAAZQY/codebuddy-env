$ErrorActionPreference = 'Stop'
$root = 'd:\plain_view\66T\mis-t160-XH-ptz'
$gbk = [Text.Encoding]::GetEncoding(936)
$files = Get-ChildItem -Path $root -Recurse -Include *.c,*.h,*.s -File
foreach ($f in $files) {
    $b = [IO.File]::ReadAllBytes($f.FullName)
    $s = $gbk.GetString($b)
    $rt = $gbk.GetByteCount($s)
    $crlf = 0
    $loneLF = 0
    $loneCR = 0
    for ($i = 0; $i -lt $s.Length; $i++) {
        $c = $s[$i]
        if ($c -eq [char]13) {
            if ($i + 1 -lt $s.Length -and $s[$i + 1] -eq [char]10) { $crlf++ } else { $loneCR++ }
        }
        elseif ($c -eq [char]10) {
            if ($i -eq 0 -or $s[$i - 1] -ne [char]13) { $loneLF++ }
        }
    }
    $flag = ''
    if ($rt -ne $b.Length) { $flag = '  ROUNDTRIP-MISMATCH ' }
    if ($loneLF -gt 0 -or $loneCR -gt 0) { $flag = $flag + '  WEIRD-NL ' }
    if ($flag -ne '') {
        Write-Output ($f.FullName.Substring($root.Length).TrimStart('\') + '  bytes=' + $b.Length + '  roundtrip=' + $rt + '  crlf=' + $crlf + '  loneLF=' + $loneLF + '  loneCR=' + $loneCR + $flag)
    }
}
Write-Output 'DIAG-DONE'
