# Ana installer for Windows (x64).
#   irm https://raw.githubusercontent.com/matiomacedo/ana/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$repo = "matiomacedo/ana"
$target = "windows-x64"

$release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
$tag = $release.tag_name
if (-not $tag) {
    Write-Error "Could not find a published release — check https://github.com/$repo/releases"
}

$url = "https://github.com/$repo/releases/download/$tag/ana-$tag-$target.zip"
$dest = Join-Path $env:LOCALAPPDATA "Programs\ana"
$tmp = Join-Path $env:TEMP "ana-install.zip"

Write-Host "Installing ana $tag ($target)..."
Invoke-WebRequest $url -OutFile $tmp
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Expand-Archive $tmp -DestinationPath $dest
Remove-Item $tmp

# Clear mark-of-the-web so SmartScreen doesn't block the binary.
Get-ChildItem $dest -Recurse -File | Unblock-File

$exeDir = Join-Path $dest "ana"
& (Join-Path $exeDir "ana.exe") --help | Out-Null

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$exeDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$exeDir", "User")
    Write-Host "Added $exeDir to your user PATH — restart your terminal."
}
Write-Host "Installed: $exeDir\ana.exe ($tag)"
Write-Host "Next: make sure Ollama is running, then run 'ana' in a project directory."
