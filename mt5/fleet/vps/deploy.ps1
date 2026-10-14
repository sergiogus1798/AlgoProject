# Copy one account's package into its terminal's data folder and, with $Restart, relaunch the terminal on that profile.
# Variables set by deploy.py before this text: $Install (the terminal's install folder), $Profile (also the package's folder name), $Restart.
# The data folder is found by origin.txt (the terminals are not portable); AutoTrading and the login stay the owner's.
$Package = Join-Path $env:USERPROFILE "fleet-packages\$Profile"
$base = "$env:APPDATA\MetaQuotes\Terminal"
$data = Get-ChildItem $base -Directory | Where-Object {
  $f = "$($_.FullName)\origin.txt"
  (Test-Path $f) -and (((Get-Content $f -Encoding Unicode) -join "") -eq $Install)
} | Select-Object -First 1
if (-not $data) { throw "ningún terminal con origin.txt = $Install" }
$d = $data.FullName
New-Item -ItemType Directory -Force "$d\MQL5\Experts\AlgoProject" | Out-Null
Copy-Item "$Package\Experts\*" "$d\MQL5\Experts\AlgoProject\" -Force
New-Item -ItemType Directory -Force "$d\MQL5\Presets" | Out-Null
Copy-Item "$Package\Presets\*" "$d\MQL5\Presets\" -Force
New-Item -ItemType Directory -Force "$d\MQL5\Profiles\Charts\$Profile" | Out-Null
Remove-Item "$d\MQL5\Profiles\Charts\$Profile\*" -Force  # a chart of an EA taken out must not survive
Copy-Item "$Package\Profiles\Charts\$Profile\*" "$d\MQL5\Profiles\Charts\$Profile\" -Force
if ($Restart) {
  Get-Process terminal64 -ErrorAction SilentlyContinue | Where-Object { (Split-Path $_.Path -Parent) -eq $Install } | ForEach-Object { $_.CloseMainWindow() | Out-Null; Start-Sleep 20; if (-not $_.HasExited) { $_.Kill() } }
  Start-Process "$Install\terminal64.exe" -ArgumentList "/profile:`"$Profile`""
}
"ok $d"
