$ErrorActionPreference = 'Stop'
$src = 'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
$out = 'D:\Codebuddy\tmp\ppt_preview'
if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out | Out-Null }

$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($src, $true, $false, $false)
foreach ($i in 4, 5, 8, 9, 10, 11, 12, 14) {
    $f = Join-Path $out ("s{0:d2}.png" -f $i)
    $pres.Slides.Item($i).Export($f, 'PNG', 1280, 720)
    Write-Output ("exported " + $f)
}
$pres.Close()
$app.Quit()
Write-Output 'done'
