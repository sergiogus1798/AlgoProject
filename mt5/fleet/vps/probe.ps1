# Health of the VPS and of its running MT5 terminals, as one JSON object on stdout. Read-only.
$os = Get-CimInstance Win32_OperatingSystem
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$base = "$env:APPDATA\MetaQuotes\Terminal"
$origins = @{}
Get-ChildItem $base -Directory | ForEach-Object {
  $f = "$($_.FullName)\origin.txt"
  if (Test-Path $f) { $origins[(Get-Content $f -Encoding Unicode) -join ""] = $_.FullName }
}
$terminals = @()
Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object {
  $install = Split-Path $_.Path -Parent
  $login = $null
  $errors = @()
  $data = $origins[$install]
  if ($data) {
    $log = "$data\logs\$(Get-Date -Format yyyyMMdd).log"
    if (Test-Path $log) {
      $lines = Get-Content $log -Encoding Unicode
      $auth = $lines | Select-String -Pattern "'(\d{4,})':" | Select-Object -Last 1
      if ($auth) { $login = [long]$auth.Matches[0].Groups[1].Value }
      $errors = @($lines | Select-String -Pattern "error|failed|cannot" | Select-Object -Last 10 | ForEach-Object { $_.Line })
    }
  }
  $terminals += [pscustomobject]@{ install = $install; pid = $_.Id; ram_mb = [math]::Round($_.WorkingSet64 / 1MB); login = $login; errors = $errors }
}
[pscustomobject]@{
  written_gmt = [int][double]::Parse((Get-Date -UFormat %s -Date (Get-Date).ToUniversalTime()))
  ram_total_mb = [math]::Round($os.TotalVisibleMemorySize / 1KB)
  ram_free_mb = [math]::Round($os.FreePhysicalMemory / 1KB)
  cpu_pct = $cpu
  disk_free_gb = [math]::Round($disk.FreeSpace / 1GB, 1)
  uptime_h = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours, 1)
  terminals = $terminals
} | ConvertTo-Json -Depth 4 -Compress
