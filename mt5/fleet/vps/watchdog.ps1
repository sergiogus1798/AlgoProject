# Relaunch any fleet terminal that is not running; run every 5 minutes by the scheduled task `AlgoFleetWatchdog`
# (installed by `python3 -m mt5.fleet.deploy --install-watchdog`). Install folders, one per line, in installs.txt beside it.
# It only starts a terminal that is down: the login is saved in the terminal and AutoTrading stays the owner's.
$here = Split-Path $MyInvocation.MyCommand.Path -Parent
$up = @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { Split-Path $_.Path -Parent })
foreach ($i in Get-Content "$here\installs.txt") { if ($i -and ($up -notcontains $i)) { Start-Process "$i\terminal64.exe" } }
