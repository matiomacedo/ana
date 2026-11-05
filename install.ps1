# Ana installer for Windows (x64).
#   irm https://raw.githubusercontent.com/matiomacedo/ana/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$repo = "matiomacedo/ana"
$target = "windows-x64"

# Pin a specific version (e.g. a prerelease):  $env:ANA_VERSION = "v0.1.0-rc1"
$tag = $env:ANA_VERSION
if (-not $tag) {
    Write-Error "Windows isn't supported in the latest release. To install the last Windows build, set `$env:ANA_VERSION = 'v0.1.0'` and run this again."
}
if (-not $tag) {
    Write-Error "Could not find a published release — check https://github.com/$repo/releases"
}

$asset = "ana-$tag-$target.zip"
$base = "https://github.com/$repo/releases/download/$tag"
$dest = Join-Path $env:LOCALAPPDATA "Programs\ana"
$tmp = Join-Path $env:TEMP ("ana-install-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
    Write-Host "Installing ana $tag ($target)..."
    $zip = Join-Path $tmp $asset
    $sums = Join-Path $tmp "checksums.txt"
    Invoke-WebRequest "$base/$asset" -OutFile $zip
    try {
        Invoke-WebRequest "$base/ana-$tag-checksums.txt" -OutFile $sums
    } catch {
        throw "Could not download the checksums for $tag, so nothing was installed. Try again, or check https://github.com/$repo/releases/tag/$tag"
    }

    $expected = $null
    foreach ($line in Get-Content $sums) {
        $parts = $line -split "\s+", 2
        if ($parts.Count -eq 2 -and ($parts[1] -replace "^[*]", "" -replace "^[.]/", "") -eq $asset) {
            $expected = $parts[0]
        }
    }
    $actual = (Get-FileHash $zip -Algorithm SHA256).Hash
    if (-not $expected -or $expected -ine $actual) {
        throw "The download does not match its published checksum, so nothing was installed. Expected: $expected  Actual: $actual"
    }

    # Unpack and run the new version first, so a bad archive or a binary that
    # won't start leaves the existing install working.
    $staged = Join-Path $tmp "staged"
    Expand-Archive $zip -DestinationPath $staged

    # Clear mark-of-the-web so SmartScreen doesn't block the binary.
    Get-ChildItem $staged -Recurse -File | Unblock-File
    & (Join-Path $staged "ana\ana.exe") --help | Out-Null

    New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Move-Item $staged $dest
} finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

$exeDir = Join-Path $dest "ana"

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$exeDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$exeDir", "User")
    Write-Host "Added $exeDir to your user PATH — restart your terminal."
}
Write-Host "Installed: $exeDir\ana.exe ($tag)"
Write-Host "Next: make sure Ollama is running, then run 'ana' in a project directory."
