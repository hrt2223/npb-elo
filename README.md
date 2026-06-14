# NPB 2026 Elo

NPB 2026 season Elo rating tracker.

Site:

https://hrt2223.github.io/npb-elo/

The production code lives in `npb/2026`. GitHub Actions updates the data every day and GitHub Pages serves the generated static site.

For the folder map, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Main Commands

Run from `npb/2026`.

```powershell
python fetch_results_2026.py --merge-existing
python update_daily.py
python make_elo_tables.py
python make_elo_graphs.py
python update_today_probabilities.py
python fetch_standings_2026.py
python make_site.py
```

`daily_update.ps1` runs the same update flow locally. The GitHub Actions workflow is the main automation, so updates can run even when this PC is off.

## Elo Parameters

Edit `npb/2026/elo_settings.py` to change the calculation parameters used by both Elo updates and win-probability predictions.

- `K_FACTOR`: rating movement per game
- `LOGISTIC_BASE`: base of the expected-score function
- `LOGISTIC_SCALE`: rating-difference scale of the expected-score function
- `INITIAL_RATING`: starting rating for each team
- `HOME_ADVANTAGE`: home-team rating adjustment

After changing a value, rerun the daily update flow to rebuild the CSV files, graphs, probabilities, and site.
