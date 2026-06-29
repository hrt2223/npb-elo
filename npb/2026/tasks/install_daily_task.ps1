$ErrorActionPreference = "Stop"

$TaskName = "NPB 2026 Elo Daily Update"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DailyScript = Join-Path $ScriptDir "daily_update.ps1"

if (-not (Test-Path $DailyScript)) {
    throw "daily_update.ps1 not found: $DailyScript"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$DailyScript`"" `
    -WorkingDirectory $ScriptDir

$Trigger = New-ScheduledTaskTrigger -Daily -At "00:00"
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Fetch today's NPB 2026 results and update Elo ratings." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Runs daily at 00:00"
