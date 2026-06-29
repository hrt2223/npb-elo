# NPB 2026 Elo

NPB 2026 season Elo rating tracker.

Site:

https://hrt2223.github.io/npb-elo/

The production code lives in `npb/2026`. GitHub Actions updates the data every day and GitHub Pages serves the generated static site.

For the folder map, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).
For the update flow and local PC sync, see [UPDATE_FLOW.md](UPDATE_FLOW.md).
For the implemented feature list, see [FEATURES.md](FEATURES.md).

## Main Commands

Run from `npb/2026`.

```powershell
python scripts/fetch_results_2026.py --merge-existing
python scripts/update_daily.py
python scripts/make_elo_tables.py
python scripts/make_elo_graphs.py
python scripts/update_today_probabilities.py
python scripts/fetch_lineups_2026.py
python scripts/fetch_standings_2026.py
python scripts/make_site.py
```

`scripts/update_today_probabilities.py` fetches today's schedule, Elo win probabilities, and probable starters.
`scripts/fetch_standings_2026.py` builds standings from `game_results_jp_2026.csv`; it does not wait for the official NPB standings page.

`tasks/daily_update.ps1` runs the same update flow locally. The GitHub Actions workflow is the main automation, so updates can run even when this PC is off.

To copy GitHub Actions generated data back to this PC:

```powershell
cd C:\2026\kenkyu\elo\npb\2026
powershell -ExecutionPolicy Bypass -File .\tasks\sync_from_github.ps1
```

## Elo Parameters

Edit `npb/2026/scripts/elo_settings.py` to change the calculation parameters used by both Elo updates and win-probability predictions.

- `K_FACTOR`: rating movement per game
- `LOGISTIC_BASE`: base of the expected-score function
- `LOGISTIC_SCALE`: rating-difference scale of the expected-score function
- `INITIAL_RATING`: starting rating for each team
- `HOME_ADVANTAGE`: home-team rating adjustment

After changing a value, rerun the daily update flow to rebuild the CSV files, graphs, probabilities, and site.


