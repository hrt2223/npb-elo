$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$RunLogDir = Join-Path $BaseDir "logs"
$RunLog = Join-Path $RunLogDir "daily_task.log"

New-Item -ItemType Directory -Path $RunLogDir -Force | Out-Null

Set-Location $BaseDir

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $RunLog -Value "================================================================"
Add-Content -Path $RunLog -Value "Started at: $timestamp"

try {
    python .\scripts\fetch_results_2026.py --today-only --merge-existing 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\update_daily.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\make_elo_tables.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\make_elo_graphs.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    Add-Content -Path $RunLog -Value "Fetching today's schedule, win probabilities, and probable starters."
    python .\scripts\update_today_probabilities.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\fetch_lineups_2026.py --minutes-before 60 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\fetch_upcoming_schedule_2026.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\fetch_standings_2026.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\scripts\make_site.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    $finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Finished at: $finished"
}
catch {
    $failed = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Failed at: $failed"
    Add-Content -Path $RunLog -Value $_.Exception.Message
    throw
}
