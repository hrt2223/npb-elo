$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunLogDir = Join-Path $ScriptDir "logs"
$RunLog = Join-Path $RunLogDir "daily_task.log"

New-Item -ItemType Directory -Path $RunLogDir -Force | Out-Null

Set-Location $ScriptDir

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $RunLog -Value "================================================================"
Add-Content -Path $RunLog -Value "Started at: $timestamp"

try {
    python .\fetch_results_2026.py --today-only --merge-existing 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\update_daily.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\make_elo_tables.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\make_elo_graphs.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    Add-Content -Path $RunLog -Value "Fetching today's schedule, win probabilities, and probable starters."
    python .\update_today_probabilities.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\fetch_lineups_2026.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\fetch_standings_2026.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    python .\make_site.py 2>&1 | Tee-Object -FilePath $RunLog -Append
    $finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Finished at: $finished"
}
catch {
    $failed = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Failed at: $failed"
    Add-Content -Path $RunLog -Value $_.Exception.Message
    throw
}
