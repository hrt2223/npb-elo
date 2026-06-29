$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$RepoRoot = (Resolve-Path (Join-Path $BaseDir "..\..")).Path
$RunLogDir = Join-Path $BaseDir "logs"
$RunLog = Join-Path $RunLogDir "sync_from_github.log"

New-Item -ItemType Directory -Path $RunLogDir -Force | Out-Null

Set-Location $RepoRoot

function Invoke-LoggedCommand {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList
    )

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $FilePath @ArgumentList 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }

    $output | Tee-Object -FilePath $RunLog -Append
    if ($exitCode -ne 0) {
        throw "$FilePath $($ArgumentList -join ' ') failed with exit code $exitCode"
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $RunLog -Value "================================================================"
Add-Content -Path $RunLog -Value "Started at: $timestamp"

try {
    Invoke-LoggedCommand -FilePath "git" -ArgumentList @("fetch", "--quiet", "origin", "main")

    # Sync generated production data from GitHub Actions.
    # This intentionally updates generated files only, so local code edits are not overwritten.
    Invoke-LoggedCommand -FilePath "git" -ArgumentList @(
        "restore",
        "--source=origin/main",
        "--",
        "npb/2026/game_results_jp_2026.csv",
        "npb/2026/output",
        "npb/2026/site"
    )

    $finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Finished at: $finished"
}
catch {
    $failed = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $RunLog -Value "Failed at: $failed"
    Add-Content -Path $RunLog -Value $_.Exception.Message
    throw
}
