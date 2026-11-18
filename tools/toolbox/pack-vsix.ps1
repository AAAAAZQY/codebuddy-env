<#
.SYNOPSIS
    把扩展源码目录打包成可安装的 VSIX（无需 vsce）。

.DESCRIPTION
    SourceDir 里放扩展源码（package.json 与其它文件直接在根下）。
    脚本自动读取 package.json 的 name/version/publisher/displayName/engines.vscode，
    生成 extension.vsixmanifest 与 [Content_Types].xml，
    并用 .NET ZipArchive 逐条写入（条目名统一用正斜杠，兼容 VS Code/CodeBuddy）。

.EXAMPLE
    .\pack-vsix.ps1 -SourceDir D:\Codebuddy\ext-src\cd11-diff -OutFile D:\Codebuddy\ext-src\cd11-diff.vsix
#>
param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$OutFile
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$pkgPath = Join-Path $SourceDir 'package.json'
if (-not (Test-Path $pkgPath)) { throw "package.json 不存在: $pkgPath" }
$pkg = Get-Content $pkgPath -Raw -Encoding UTF8 | ConvertFrom-Json

$id = $pkg.publisher + '.' + $pkg.name
$version = $pkg.version
$engine = '^1.70.0'
if ($pkg.engines -and $pkg.engines.vscode) { $engine = $pkg.engines.vscode }

$stage = Join-Path $env:TEMP ('vsix-stage-' + [guid]::NewGuid().ToString('N'))
$extDir = Join-Path $stage 'extension'
New-Item -ItemType Directory -Force -Path $extDir | Out-Null
$stage = (Resolve-Path -LiteralPath $stage).Path.TrimEnd('\')
$extDir = Join-Path $stage 'extension'

$SourceDir = (Resolve-Path -LiteralPath $SourceDir).Path.TrimEnd('\')
foreach ($srcFile in [System.IO.Directory]::GetFiles($SourceDir, '*', [System.IO.SearchOption]::AllDirectories)) {
    $rel = $srcFile.Substring($SourceDir.Length).TrimStart('\')
    $dest = Join-Path $extDir $rel
    $destParent = Split-Path $dest -Parent
    if (-not (Test-Path $destParent)) { New-Item -ItemType Directory -Force -Path $destParent | Out-Null }
    Copy-Item $srcFile $dest -Force
}

$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="$($pkg.name)" Version="$version" Publisher="$($pkg.publisher)" />
    <DisplayName>$($pkg.displayName)</DisplayName>
    <Description xml:space="preserve">$($pkg.description)</Description>
    <Tags></Tags>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="$engine" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
  </Assets>
</PackageManifest>
"@
[System.IO.File]::WriteAllText((Join-Path $stage 'extension.vsixmanifest'), $manifest, (New-Object System.Text.UTF8Encoding($false)))

$contentTypes = @"
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="js" ContentType="application/javascript" />
  <Default Extension="xml" ContentType="text/xml" />
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="svg" ContentType="image/svg+xml" />
  <Default Extension="png" ContentType="image/png" />
</Types>
"@
[System.IO.File]::WriteAllText((Join-Path $stage '[Content_Types].xml'), $contentTypes, (New-Object System.Text.UTF8Encoding($false)))

if (Test-Path $OutFile) { Remove-Item $OutFile -Force }
$zip = [System.IO.Compression.ZipFile]::Open($OutFile, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($stageFile in [System.IO.Directory]::GetFiles($stage, '*', [System.IO.SearchOption]::AllDirectories)) {
        $rel = $stageFile.Substring($stage.Length).TrimStart('\').Replace('\', '/')
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $stageFile, $rel, [System.IO.Compression.CompressionLevel]::Optimal)
    }
} finally {
    $zip.Dispose()
}
Remove-Item $stage -Recurse -Force

Write-Output ("VSIX: $OutFile (" + (Get-Item $OutFile).Length + " bytes), id=$id, version=$version, engine=$engine")
