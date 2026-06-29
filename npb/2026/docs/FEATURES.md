# Implemented Features

縺薙・繝輔ぃ繧､繝ｫ縺ｯ縲∫樟蝨ｨ螳溯｣・＆繧後※縺・ｋ讖溯・縺ｮ荳隕ｧ縺ｧ縺吶ゆｻ雁ｾ後≠繧峨◆縺ｪ讖溯・繧定ｿｽ蜉縺励◆蝣ｴ蜷医・縲√％縺ｮ繝輔ぃ繧､繝ｫ縺ｫ霑ｽ險倥＠縺ｾ縺吶・
## Data Collection

| feature | status | main files | output |
| --- | --- | --- | --- |
| 2026蟷ｴ荳霆榊・蠑乗姶縺ｮ隧ｦ蜷育ｵ先棡蜿門ｾ・| 螳溯｣・ｸ医∩ | `scripts/fetch_results_2026.py` | `game_results_jp_2026.csv` |
| 莉頑律縺ｮ隧ｦ蜷井ｺ亥ｮ壼叙蠕・| 螳溯｣・ｸ医∩ | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 莉頑律縺ｮ莠亥相蜈育匱蜿門ｾ・| 螳溯｣・ｸ医∩ | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 莉頑律縺ｮ繧ｹ繧ｿ繝｡繝ｳ蜿門ｾ・| 螳溯｣・ｸ医∩ | `scripts/fetch_lineups_2026.py` | `output/today_lineups.csv` |
| 繧ｻ繝ｻ繝ｪ繝ｼ繧ｰ縲√ヱ繝ｻ繝ｪ繝ｼ繧ｰ縺ｮ鬆・ｽ崎｡ｨ蜿門ｾ・| 螳溯｣・ｸ医∩ | `scripts/fetch_standings_2026.py` | `output/standings.csv` |

## Elo Calculation

| feature | status | main files | output |
| --- | --- | --- | --- |
| Elo繝ｬ繝ｼ繝・ぅ繝ｳ繧ｰ險育ｮ・| 螳溯｣・ｸ医∩ | `scripts/elo.py`, `scripts/update_daily.py` | `output/elo_final_ranking.csv`, `output/elo_by_game.csv`, `output/elo_history.csv` |
| 繧ｻ繝ｻ繝ｪ繝ｼ繧ｰ縺縺代・Elo蜃ｺ蜉・| 螳溯｣・ｸ医∩ | `scripts/update_daily.py` | `output/central/` |
| 繝代・繝ｪ繝ｼ繧ｰ縺縺代・Elo蜃ｺ蜉・| 螳溯｣・ｸ医∩ | `scripts/update_daily.py` | `output/pacific/` |
| 莠､豬∵姶譛滄俣縺ｮElo蜃ｺ蜉・| 螳溯｣・ｸ医∩ | `scripts/update_daily.py` | `output/interleague/` |
| Elo謗ｨ遘ｻ陦ｨ縺ｮ逕滓・ | 螳溯｣・ｸ医∩ | `scripts/make_elo_tables.py` | `output/elo_table.csv` |
| Elo謗ｨ遘ｻ繧ｰ繝ｩ繝輔・逕滓・ | 螳溯｣・ｸ医∩ | `scripts/make_elo_graphs.py` | `output/elo_graph.png` |
| K蛟､縲√Ο繧ｸ繧ｹ繝・ぅ繝・け髢｢謨ｰ縲∝・譛溷､縲√・繝ｼ繝陬懈ｭ｣縺ｮ螟夜Κ險ｭ螳・| 螳溯｣・ｸ医∩ | `scripts/elo_settings.py` | Elo險育ｮ励→蜍晉紫莠域ｸｬ縺ｫ蜿肴丐 |

## Prediction

| feature | status | main files | output |
| --- | --- | --- | --- |
| 莉頑律縺ｮ蟇ｾ謌ｦ繧ｫ繝ｼ繝峨＃縺ｨ縺ｮElo蜍晉紫陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/update_today_probabilities.py`, `scripts/make_site.py` | 繧ｵ繧､繝医・莉頑律縺ｮ蟇ｾ謌ｦ莠亥ｮ壹き繝ｼ繝・|
| 繧ｻ繝ｻ繝ｪ繝ｼ繧ｰ縲√ヱ繝ｻ繝ｪ繝ｼ繧ｰ縺ｮ繧ｿ繝門挨隧ｦ蜷井ｺ亥ｮ夊｡ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/make_site.py` | `site/index.html` |
| 莠亥相蜈育匱縺ｨ蜍晉紫縺ｮ蜷梧凾陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/update_today_probabilities.py`, `scripts/make_site.py` | `site/index.html` |

## Site

| feature | status | main files | output |
| --- | --- | --- | --- |
| 鮟貞渕隱ｿ縺ｮElo繝繝・す繝･繝懊・繝・| 螳溯｣・ｸ医∩ | `scripts/make_site.py`, `site_builder/dashboard.py` | `site/index.html` |
| 繝繝・す繝･繝懊・繝蛾・鄂ｮ縺ｮ蜀崎ｨｭ險・| 螳溯｣・ｸ医∩ | `site_builder/dashboard.py` | 繧ｵ繝槭Μ縲∽ｻ頑律縺ｮ蟇ｾ謌ｦ莠亥ｮ壹・・ｽ崎｡ｨ縲√げ繝ｩ繝輔・驟咲ｽｮ |
| 蜈ｨ菴薙√そ繝ｻ繝ｪ繝ｼ繧ｰ縲√ヱ繝ｻ繝ｪ繝ｼ繧ｰ縲∽ｺ､豬∵姶繧ｿ繝・| 螳溯｣・ｸ医∩ | `scripts/make_site.py` | `site/index.html` |
| Elo謗ｨ遘ｻ繧ｰ繝ｩ繝戊｡ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/make_site.py`, `scripts/make_elo_graphs.py` | `site/index.html` |
| 譌･莉倥・邵ｦ繝ｩ繧､繝ｳ縺ｧ謗ｨ遘ｻ遒ｺ隱・| 螳溯｣・ｸ医∩ | `scripts/make_site.py` | `site/index.html` |
| Elo繝ｩ繝ｳ繧ｭ繝ｳ繧ｰ陦ｨ陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/make_site.py` | `site/index.html` |
| Elo謗ｨ遘ｻ陦ｨ陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/make_site.py` | `site/index.html` |
| 莉頑律縺ｮ蟇ｾ謌ｦ莠亥ｮ壹∝享邇・∽ｺ亥相蜈育匱陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `site_builder/schedule.py` | `site/index.html` |
| 鬆・ｽ崎｡ｨ陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `site_builder/standings.py` | `site/index.html` |
| 繧ｹ繧ｿ繝｡繝ｳ陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `site_builder/schedule.py` | `site/index.html` |
| 繧ｻ繝ｻ繝ｪ繝ｼ繧ｰ縲√ヱ繝ｻ繝ｪ繝ｼ繧ｰ縺ｮ蜷・帥蝗｣繝壹・繧ｸ | 螳溯｣・ｸ医∩ | `site_builder/team_pages.py` | `site/central/`, `site/pacific/` |
| 逅・屮繝壹・繧ｸ縺ｮ逶ｴ霑・0隧ｦ蜷域・邵ｾ陦ｨ遉ｺ | 螳溯｣・ｸ医∩ | `site_builder/team_pages.py` | 蜷・帥蝗｣繝壹・繧ｸ |
| 逅・屮繝壹・繧ｸ縺ｮElo荳頑・邇・｡ｨ遉ｺ | 螳溯｣・ｸ医∩ | `site_builder/team_pages.py` | 蜷・帥蝗｣繝壹・繧ｸ |
| 謖・ｮ壹メ繝ｼ繝繧ｫ繝ｩ繝ｼ縺ｮ繧ｰ繝ｩ繝輔√き繝ｼ繝芽｡ｨ遉ｺ | 螳溯｣・ｸ医∩ | `scripts/make_site.py`, `scripts/make_elo_graphs.py` | 繧ｵ繧､繝医√げ繝ｩ繝姫NG |

## Automation

| feature | status | main files | output |
| --- | --- | --- | --- |
| GitHub Actions縺ｫ繧医ｋ閾ｪ蜍墓峩譁ｰ | 螳溯｣・ｸ医∩ | `.github/workflows/npb-elo-daily.yml` | GitHub荳翫・CSV縲？TML縲∫判蜒・|
| 譛・譎ゅ・莠亥ｮ壹∝享邇・∽ｺ亥相蜈育匱譖ｴ譁ｰ | 螳溯｣・ｸ医∩ | `.github/workflows/npb-elo-daily.yml` | `output/today_probabilities.csv`, `site/` |
| 隧ｦ蜷亥燕蠕後・繧ｹ繧ｿ繝｡繝ｳ遒ｺ隱・| 螳溯｣・ｸ医∩ | `.github/workflows/npb-elo-daily.yml`, `scripts/fetch_lineups_2026.py` | `output/today_lineups.csv` |
| 螟懊・隧ｦ蜷育ｵ先棡譖ｴ譁ｰ | 螳溯｣・ｸ医∩ | `.github/workflows/npb-elo-daily.yml` | `game_results_jp_2026.csv`, `output/`, `site/` |
| GitHub Pages蜈ｬ髢・| 螳溯｣・ｸ医∩ | `index.html`, `site/` | `https://hrt2223.github.io/npb-elo/` |
| 繝ｭ繝ｼ繧ｫ繝ｫPC縺ｧ縺ｮ荳諡ｬ譖ｴ譁ｰ | 螳溯｣・ｸ医∩ | `tasks/daily_update.ps1` | 繝ｭ繝ｼ繧ｫ繝ｫ縺ｮCSV縲？TML縲∫判蜒・|
| GitHub譖ｴ譁ｰ繝・・繧ｿ縺ｮ繝ｭ繝ｼ繧ｫ繝ｫ蜷梧悄 | 螳溯｣・ｸ医∩ | `tasks/sync_from_github.ps1` | 繝ｭ繝ｼ繧ｫ繝ｫ縺ｮ逕滓・繝・・繧ｿ |
| Windows繝ｭ繧ｰ繧ｪ繝ｳ譎ゅ・繝ｭ繝ｼ繧ｫ繝ｫ蜷梧悄 | 螳溯｣・ｸ医∩ | `tasks/install_startup_sync.ps1` | 繧ｹ繧ｿ繝ｼ繝医い繝・・逋ｻ骭ｲ |

## Documentation

| feature | status | file |
| --- | --- | --- |
| 繝励Ο繧ｸ繧ｧ繧ｯ繝域ｦりｦ・| 螳溯｣・ｸ医∩ | `docs/README.md` |
| 繝輔か繝ｫ繝繝ｼ讒区・ | 螳溯｣・ｸ医∩ | `docs/PROJECT_STRUCTURE.md` |
| 譖ｴ譁ｰ繝輔Ο繝ｼ縺ｨPC蜷梧悄縺ｮ隱ｬ譏・| 螳溯｣・ｸ医∩ | `docs/UPDATE_FLOW.md` |
| 螳溯｣・ｸ医∩讖溯・荳隕ｧ | 螳溯｣・ｸ医∩ | `docs/FEATURES.md` |

## Update Rule

譁ｰ縺励＞讖溯・繧定ｿｽ蜉縺励◆繧峨∬ｩｲ蠖薙☆繧九き繝・ざ繝ｪ縺ｮ陦ｨ縺ｫ1陦瑚ｿｽ蜉縺励∪縺吶・
霑ｽ險倥☆繧句・螳ｹ:

| item | description |
| --- | --- |
| `feature` | 菴輔′縺ｧ縺阪ｋ繧医≧縺ｫ縺ｪ縺｣縺溘° |
| `status` | `螳溯｣・ｸ医∩`縲～荳驛ｨ螳溯｣・縲～讀懆ｨ惹ｸｭ` 縺ｮ縺・★繧後° |
| `main files` | 荳ｻ縺ｫ髢｢菫ゅ☆繧九さ繝ｼ繝・|
| `output` | 逕滓・縺輔ｌ繧気SV縲？TML縲∫判蜒上√∪縺溘・陦ｨ遉ｺ蝣ｴ謇 |


