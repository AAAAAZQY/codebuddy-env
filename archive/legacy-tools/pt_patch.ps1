$ErrorActionPreference = 'Stop'

$target = 'D:\bProject\pid_tuner\pid_tuner.py'
$block  = 'D:\Codebuddy\tools\pt_block.py'
$bakDir = 'D:\Codebuddy\backup\pid_tuner-20261028'
$bak    = Join-Path $bakDir 'pid_tuner.py'

New-Item -ItemType Directory -Force -Path $bakDir | Out-Null

$lat = [Text.Encoding]::GetEncoding(28591)
$rawBytes = [IO.File]::ReadAllBytes($target)
[IO.File]::WriteAllBytes($bak, $rawBytes)

$src = $lat.GetString($rawBytes)
$before = $rawBytes.Length

$nl = "`n"
if ($src.Contains("`r`n")) { $nl = "`r`n" }
Write-Output ("newline = " + $(if ($nl -eq "`r`n") { 'CRLF' } else { 'LF' }))

$blk = [IO.File]::ReadAllText($block, [Text.Encoding]::ASCII)
$blk = $blk.Replace("`r`n", "`n")
if ($nl -ne "`n") { $blk = $blk.Replace("`n", $nl) }

# 1) insert the vofa helpers right before read_data_file()
$a1 = 'def read_data_file(path: str, dt: float = 1.0):'
if ($src.IndexOf($a1) -lt 0) { throw 'anchor1 missing: read_data_file' }
if ([regex]::Matches($src, [regex]::Escape($a1)).Count -ne 1) { throw 'anchor1 not unique' }
$src = $src.Replace($a1, $blk + $a1)

# 2) inside read_data_file, try vofa before decoding text
$a2 = "    last_err = None"
if ($src.IndexOf($a2) -lt 0) { throw 'anchor2 missing: last_err' }
$ins2 = @(
    "    if _maybe_vofa(raw):",
    "        _vofa_text = _vofa_to_csv(raw, dt, _VOFA_MAP)",
    "        if _vofa_text:",
    "            _VOFA_USED[0] = True",
    "            return parse_data(_vofa_text, dt=dt)",
    "",
    ""
) -join $nl
$src = $src.Replace($a2, $ins2 + $a2)

# 3) main(): accept --vofa-map
$a3 = '        path = args[idx + 1]'
if ($src.IndexOf($a3) -lt 0) { throw 'anchor3 missing: path = args[idx + 1]' }
$ins3 = @(
    '        global _VOFA_MAP',
    '        if "--vofa-map" in args:',
    '            _vofa_map_idx = args.index("--vofa-map")',
    '            if len(args) > _vofa_map_idx + 1:',
    '                _VOFA_MAP = args[_vofa_map_idx + 1]'
) -join $nl
$src = $src.Replace($a3, $a3 + $nl + $ins3)

$outBytes = $lat.GetBytes($src)
[IO.File]::WriteAllBytes($target, $outBytes)

Write-Output ("bytes: " + $before + " -> " + $outBytes.Length + "  (+" + ($outBytes.Length - $before) + ")")
Write-Output ("backup: " + $bak)

# sanity: file must still decode as utf-8 and parse as python
$env:PYTHONIOENCODING = 'utf-8'
python -c "import ast,io,sys; s=io.open(r'D:\bProject\pid_tuner\pid_tuner.py',encoding='utf-8').read(); ast.parse(s); print('utf8+ast OK, lines=%d' % (s.count(chr(10))+1))"
