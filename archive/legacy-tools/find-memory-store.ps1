$ErrorActionPreference = 'SilentlyContinue'
$roots = @(
    'C:\Users\myages2026\AppData\Roaming\CodeBuddy CN\User',
    'C:\Users\myages2026\.codebuddycn',
    'C:\Users\myages2026\.codebuddy'
)
$hits = 0
foreach ($r in $roots) {
    Get-ChildItem $r -Recurse -File -Include *.json,*.vscdb,*.db,*.md,*.txt -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -lt 20MB } |
        ForEach-Object {
            $p = $_.FullName
            $fs = [IO.File]::Open($p, 'Open', 'Read', 'ReadWrite')
            $len = [Math]::Min(2000000, $fs.Length)
            $buf = New-Object byte[] $len
            [void]$fs.Read($buf, 0, $len)
            $fs.Close()
            $txt = [Text.Encoding]::UTF8.GetString($buf)
            if ($txt.Contains('memory') -or $txt.Contains('memories') -or $txt.Contains('长期记忆')) {
                $idx = $txt.IndexOf('memor')
                if ($idx -lt 0) { $idx = $txt.IndexOf('长期记忆') }
                $st = [Math]::Max(0, $idx - 120)
                $frag = $txt.Substring($st, [Math]::Min(400, $txt.Length - $st))
                $frag = $frag -replace "[^\u0020-\u007E\u4e00-\u9fff]", ' '
                $frag = $frag -replace '\s+', ' '
                Write-Output ('=== ' + $p)
                Write-Output ('    ' + $frag)
                $hits++
            }
        }
}
Write-Output ('MEMORY-STORE-HITS=' + $hits)
