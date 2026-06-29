$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SyncScript = Join-Path $ScriptDir "sync_from_github.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupCommand = Join-Path $StartupDir "NPB 2026 Elo Sync From GitHub.cmd"

if (-not (Test-Path $SyncScript)) {
    throw "sync_from_github.ps1 not found: $SyncScript"
}

$content = @"
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SyncScript"
"@

Set-Content -Path $StartupCommand -Value $content -Encoding ASCII

Write-Host "Installed startup sync command:"
Write-Host $StartupCommand
Write-Host "It runs when this Windows user logs in."
