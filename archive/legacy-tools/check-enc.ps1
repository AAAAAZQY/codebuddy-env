param(
    [Parameter(Mandatory = $true)][string]$Path
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Path)) { Write-Output ('MISSING ' + $Path); exit 1 }
$b = [IO.File]::ReadAllBytes((Resolve-Path $Path))
$nonAscii = 0
foreach ($x in $b) { if ($x -gt 127) { $nonAscii++ } }
$head = [Text.Encoding]::ASCII.GetString($b, 0, [Math]::Min(14, $b.Length))
$enc = $head.StartsWith('%TSD-Header')
if ($nonAscii -eq 0) {
    Write-Output ('ASCII  bytes=' + $b.Length + '  ->  use edit tools (replace_in_file / write_to_file), card will appear')
} else {
    Write-Output ('GBK    bytes=' + $b.Length + '  nonAscii=' + $nonAscii + '  ->  DO NOT use edit tools; use latin1 byte patch + diff-snap')
}
if ($enc) { Write-Output 'WARNING file is DLP-encrypted, read plaintext through bridge /raw first' }
