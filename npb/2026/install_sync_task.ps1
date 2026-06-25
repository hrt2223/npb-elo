$ErrorActionPreference = "Stop"

$TaskName = "NPB 2026 Elo Sync From GitHub"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SyncScript = Join-Path $ScriptDir "sync_from_github.ps1"

if (-not (Test-Path $SyncScript)) {
    throw "sync_from_github.ps1 not found: $SyncScript"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$SyncScript`"" `
    -WorkingDirectory $ScriptDir

$Triggers = @(
    New-ScheduledTaskTrigger -AtLogOn
    New-ScheduledTaskTrigger -Daily -At "09:15"
    New-ScheduledTaskTrigger -Daily -At "00:10"
)

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Description "Sync generated NPB 2026 Elo data from GitHub Actions to this PC." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Runs at logon, 09:15, and 00:10 when this PC is available."
