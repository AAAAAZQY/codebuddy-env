$ErrorActionPreference = 'Stop'
$enc = [Text.Encoding]::GetEncoding(28591)   # latin1: byte-safe roundtrip, never touches non-ASCII
$src = 'D:\Codebuddy\tools\ext-name14-base.js'
$dst = 'D:\Codebuddy\tools\ext-name15-fixed.js'
$nl = "`r`n"

$oldC = (@(
    "        if (!fs.existsSync(pair.mirror)) {",
    "            log.appendLine('mirror not found, building: ' + pair.mirror);",
    "            await buildMirror(log, pair.real, pair.mirror);",
    "        }"
) -join $nl)
$newC = (@(
    "        if (!fs.existsSync(pair.mirror)) {",
    "            if (buildMissing) {",
    "                log.appendLine('mirror not found, building: ' + pair.mirror);",
    "                await buildMirror(log, pair.real, pair.mirror);",
    "            } else {",
    "                log.appendLine('mirror not found, skipped (manual build only): ' + pair.mirror);",
    "            }",
    "        }"
) -join $nl)

$oldD = (@(
    "            await ensureMirrorAndSync(log);",
    "            watchBranch(log);"
) -join $nl)
$newD = (@(
    "            await ensureMirrorAndSync(log, false);",
    "            watchBranch(log);"
) -join $nl)

$pairs = @(
    @{ label = 'build-number'; old = "const BUILD = 'name-14';"; new = "const BUILD = 'name-15';" },
    @{ label = 'signature'; old = 'async function ensureMirrorAndSync(log) {'; new = 'async function ensureMirrorAndSync(log, buildMissing) {' },
    @{ label = 'conditional-build'; old = $oldC; new = $newC },
    @{ label = 'no-auto-build-on-activate'; old = $oldD; new = $newD }
)

$s = $enc.GetString([IO.File]::ReadAllBytes($src))
$origLen = $s.Length
$fails = 0

foreach ($p in $pairs) {
    $i = $s.IndexOf($p.old)
    if ($i -lt 0) {
        Write-Output ('FAIL ' + $p.label + ': anchor not found')
        $fails = $fails + 1
        continue
    }
    if ($s.IndexOf($p.old, $i + 1) -ge 0) {
        Write-Output ('WARN ' + $p.label + ': anchor not unique')
    }
    $s = $s.Replace($p.old, $p.new)
    Write-Output ('OK   ' + $p.label)
}

if ($fails -gt 0) {
    Write-Output ('ABORT: ' + $fails + ' replacement(s) failed, nothing written')
} else {
    $bytes = $enc.GetBytes($s)
    [IO.File]::WriteAllBytes($dst, $bytes)
    $back = $enc.GetString([IO.File]::ReadAllBytes($dst))
    Write-Output ('WROTE ' + $dst + '  bytes ' + $origLen + ' -> ' + $bytes.Length + '  delta=' + ($bytes.Length - $origLen))
    Write-Output ('roundtrip-same=' + ($back -ceq $s))
    Write-Output ('build-15=' + $s.Contains('name-15'))
    Write-Output ('manual-only=' + $s.Contains('manual build only'))
    Write-Output ('gitTop-kept=' + $s.Contains('function gitTop'))
}
Write-Output 'PATCH-DONE'
