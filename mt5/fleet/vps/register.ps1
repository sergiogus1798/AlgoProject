# Register the scheduled task that runs watchdog.ps1 (copied beside the packages) every 5 minutes.
$Script = Join-Path $env:USERPROFILE "fleet-packages\watchdog.ps1"
$a = New-ScheduledTaskAction -Execute powershell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`""
$t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName AlgoFleetWatchdog -Action $a -Trigger $t -Force | Out-Null
"ok"
