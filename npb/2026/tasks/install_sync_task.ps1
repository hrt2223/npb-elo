$ErrorActionPreference = "Stop"

$TaskName = "NPB 2026 Elo Sync From GitHub"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SyncScript = Join-Path $ScriptDir "sync_from_github.ps1"

if (-not (Test-Path $SyncScript)) {
    throw "sync_from_github.ps1 not found: $SyncScript"
}

$TaskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$SyncScript`""

$Tasks = @(
    @{ Name = "$TaskName Logon"; Schedule = "ONLOGON"; Time = $null },
    @{ Name = "$TaskName Morning"; Schedule = "DAILY"; Time = "09:15" },
    @{ Name = "$TaskName Night"; Schedule = "DAILY"; Time = "00:10" }
)

foreach ($Task in $Tasks) {
    $Args = @(
        "/Create",
        "/TN", $Task.Name,
        "/TR", $TaskCommand,
        "/SC", $Task.Schedule,
        "/F",
        "/RL", "LIMITED"
    )

    if ($Task.Time) {
        $Args += @("/ST", $Task.Time)
    }

    & schtasks.exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to register scheduled task: $($Task.Name)"
    }
}

Write-Host "Registered scheduled tasks:"
Write-Host "- $TaskName Logon"
Write-Host "- $TaskName Morning"
Write-Host "- $TaskName Night"
