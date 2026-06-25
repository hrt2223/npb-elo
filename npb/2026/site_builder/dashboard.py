from __future__ import annotations

import html
import json

from .config import TEAM_COLORS


def build_html(payload: list[dict[str, str]]) -> str:
    data_json = json.dumps(payload, ensure_ascii=False)
    colors_json = json.dumps(TEAM_COLORS, ensure_ascii=False)
    first = payload[0]
    tabs = "".join(
        f'<button class="tab{" is-active" if item["key"] == first["key"] else ""}" data-key="{item["key"]}">{html.escape(item["label"])}</button>'
        for item in payload
    )

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2026 NPB Elo Dashboard</title>
  <style>
    :root {{
      --bg: #07090d;
      --surface: #10141d;
      --surface-2: #151b26;
      --ink: #edf2f7;
      --muted: #9aa4b2;
      --line: #252d3a;
      --line-strong: #374151;
      --accent: #38bdf8;
      --accent-dark: #7dd3fc;
      --glow: rgba(56, 189, 248, 0.22);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Yu Gothic", "Meiryo", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background:
        radial-gradient(circle at 50% -20%, rgba(56, 189, 248, 0.12), transparent 34%),
        linear-gradient(180deg, #0b111a 0%, var(--bg) 38%, #050608 100%);
      color: var(--ink);
      min-height: 100vh;
    }}
    header {{
      border-bottom: 1px solid rgba(125, 211, 252, 0.18);
      background: rgba(8, 12, 18, 0.88);
      backdrop-filter: blur(14px);
      box-shadow: 0 16px 50px rgba(0, 0, 0, 0.28);
    }}
    .header-inner {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 16px;
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: 25px;
      line-height: 1.2;
      letter-spacing: 0;
      color: #f8fafc;
    }}
    .updated {{
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 32px;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}
    .tab {{
      border: 1px solid var(--line);
      background: rgba(16, 20, 29, 0.86);
      color: var(--ink);
      border-radius: 6px;
      padding: 9px 14px;
      font: inherit;
      cursor: pointer;
      transition: border-color 160ms ease, background 160ms ease, box-shadow 160ms ease;
    }}
    .tab:hover {{
      border-color: rgba(125, 211, 252, 0.55);
      background: #151b26;
    }}
    .tab.is-active {{
      background: #0f3144;
      border-color: var(--accent);
      color: #e0f7ff;
      box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.16), 0 10px 28px var(--glow);
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric {{
      background: linear-gradient(180deg, rgba(21, 27, 38, 0.96), rgba(12, 16, 24, 0.96));
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      min-height: 76px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric-value {{
      font-size: 18px;
      font-weight: 700;
      line-height: 1.3;
      overflow-wrap: anywhere;
      color: #f8fafc;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr);
      gap: 16px;
      align-items: start;
    }}
    .panel {{
      background: rgba(16, 20, 29, 0.94);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }}
    .panel-header {{
      padding: 13px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(21, 27, 38, 0.72);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .panel-title {{
      font-size: 15px;
      font-weight: 700;
      color: #f8fafc;
    }}
    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 13px;
    }}
    a {{
      color: var(--accent-dark);
      text-decoration: none;
      font-weight: 600;
    }}
    a:hover {{ text-decoration: underline; }}
    .schedule-date {{
      color: var(--muted);
      font-size: 13px;
      padding: 12px 16px 0;
    }}
    .schedule-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      padding: 12px;
    }}
    .schedule-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(180deg, #0d131d 0%, #090d14 100%);
      padding: 13px;
      min-width: 0;
    }}
    .schedule-meta {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 11px;
    }}
    .schedule-teams {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }}
    .team-name {{
      display: flex;
      align-items: center;
      gap: 7px;
      min-width: 0;
      font-weight: 800;
      color: #f8fafc;
    }}
    .team-name.is-away {{
      justify-content: flex-end;
    }}
    .versus {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }}
    .schedule-venue {{
      color: #cbd5e1;
      font-size: 12px;
      min-height: 18px;
      margin-bottom: 12px;
    }}
    .starter-row {{
      display: grid;
      gap: 3px;
      margin-bottom: 12px;
      padding: 8px 10px;
      border: 1px solid rgba(125, 211, 252, 0.16);
      border-radius: 6px;
      background: rgba(15, 23, 42, 0.62);
      color: #dbeafe;
      font-size: 12px;
    }}
    .starter-row span {{
      color: var(--muted);
      font-size: 11px;
    }}
    .starter-row strong {{
      color: #f8fafc;
      font-weight: 800;
      overflow-wrap: anywhere;
    }}
    .probability-row {{
      display: grid;
      grid-template-columns: 44px minmax(96px, 1fr) 44px;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 800;
      color: #e5edf7;
    }}
    .probability-row span:last-child {{
      text-align: right;
    }}
    .probability-bar {{
      display: flex;
      height: 9px;
      border-radius: 999px;
      background: #1f2937;
      overflow: hidden;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
    }}
    .probability-bar span {{
      display: block;
      height: 100%;
      flex: 0 0 auto;
    }}
    .probability-bar .home-prob {{
      border-radius: 999px 0 0 999px;
    }}
    .probability-bar .away-prob {{
      border-radius: 0 999px 999px 0;
    }}
    .elo-row {{
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 11px;
      margin-top: 8px;
    }}
    .lineup-box {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(148, 163, 184, 0.18);
    }}
    .lineup-team {{
      min-width: 0;
    }}
    .lineup-team-title {{
      color: #f8fafc;
      font-size: 12px;
      font-weight: 800;
      margin-bottom: 6px;
    }}
    .lineup-list {{
      display: grid;
      gap: 4px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .lineup-list li {{
      display: grid;
      grid-template-columns: 18px 22px minmax(0, 1fr);
      gap: 5px;
      align-items: center;
      color: #dbe3ee;
      font-size: 11px;
      min-width: 0;
    }}
    .lineup-list span {{
      color: var(--muted);
    }}
    .lineup-list strong {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: #f8fafc;
    }}
    .lineup-empty {{
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid rgba(148, 163, 184, 0.18);
      color: var(--muted);
      font-size: 12px;
    }}
    .standings-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding: 12px;
    }}
    .standings-table {{
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #0b1018;
    }}
    .standings-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 12px;
      background: #111827;
      border-bottom: 1px solid var(--line);
      color: #f8fafc;
      font-weight: 800;
      font-size: 13px;
    }}
    .standings-title span:last-child {{
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      white-space: nowrap;
    }}
    .standings-team {{
      display: flex;
      align-items: center;
      gap: 8px;
      text-align: left;
      font-weight: 800;
      color: #f8fafc;
    }}
    .graph-wrap {{
      padding: 12px;
    }}
    .chart {{
      width: 100%;
      height: min(62vh, 620px);
      min-height: 360px;
      display: block;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      background: #090d14;
    }}
    .tooltip {{
      position: fixed;
      z-index: 10;
      max-width: min(320px, calc(100vw - 24px));
      background: rgba(10, 14, 21, 0.96);
      color: var(--ink);
      border: 1px solid rgba(125, 211, 252, 0.28);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.42);
      border-radius: 8px;
      padding: 10px 12px;
      pointer-events: none;
      display: none;
      font-size: 12px;
    }}
    .tooltip-title {{
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .tooltip-row {{
      display: grid;
      grid-template-columns: 10px 1fr auto;
      gap: 7px;
      align-items: center;
      margin: 3px 0;
    }}
    .swatch {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1px solid rgba(0, 0, 0, 0.15);
    }}
    .team-links {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      padding: 12px;
    }}
    .team-link {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #0b1018;
      color: #edf2f7;
    }}
    .team-link:hover {{
      border-color: rgba(125, 211, 252, 0.45);
      background: #111827;
      text-decoration: none;
    }}
    .team-dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
      box-shadow: 0 0 18px currentColor;
      flex: 0 0 auto;
    }}
    .result {{
      display: inline-grid;
      place-items: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-weight: 800;
    }}
    .result.win {{
      color: #062e18;
      background: #4ade80;
    }}
    .result.loss {{
      color: #3f0b0b;
      background: #f87171;
    }}
    .result.draw {{
      color: #1f2937;
      background: #cbd5e1;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
      color: #dbe3ee;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #202733;
      text-align: right;
    }}
    th {{
      background: #151b26;
      color: #cbd5e1;
      font-weight: 700;
    }}
    tbody tr:hover {{
      background: rgba(56, 189, 248, 0.06);
    }}
    th:first-child, td:first-child {{
      text-align: left;
    }}
    .stack {{
      display: grid;
      gap: 16px;
    }}
    .empty {{
      padding: 24px;
      color: var(--muted);
    }}
    @media (max-width: 900px) {{
      .header-inner {{
        display: block;
      }}
      .updated {{
        margin-top: 8px;
        white-space: normal;
      }}
      .summary {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .layout {{
        grid-template-columns: 1fr;
      }}
      .schedule-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .standings-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 560px) {{
      main, .header-inner {{
        padding-left: 14px;
        padding-right: 14px;
      }}
      .summary {{
        grid-template-columns: 1fr;
      }}
      h1 {{ font-size: 21px; }}
      .chart {{
        min-height: 300px;
      }}
      .schedule-grid {{
        grid-template-columns: 1fr;
      }}
      .lineup-box {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <h1>2026 NPB Elo Dashboard</h1>
      <div class="updated" id="pageUpdated">更新日時: {html.escape(first["updated"])}</div>
    </div>
  </header>
  <main>
    <nav class="tabs" aria-label="表示切り替え">
      {tabs}
    </nav>

    <section class="summary">
      <div class="metric">
        <div class="metric-label">表示</div>
        <div class="metric-value" id="metricLabel">{html.escape(first["label"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">最新日</div>
        <div class="metric-value" id="metricLatestDate">{html.escape(first["latestDate"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">対象試合数</div>
        <div class="metric-value" id="metricGames">{html.escape(first["games"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">対象期間</div>
        <div class="metric-value" id="metricPeriod">{html.escape(first["period"])}</div>
      </div>
    </section>

    <section class="panel" style="margin-bottom: 16px;">
      <div class="panel-header">
        <div class="panel-title">今日の対戦予定と勝率</div>
        <div class="links">
          <a href="../output/today_probabilities.csv">CSV</a>
          <a href="../output/today_lineups.csv">スタメンCSV</a>
        </div>
      </div>
      <div id="scheduleContent">{first["scheduleHtml"]}</div>
    </section>

    <section class="panel" style="margin-bottom: 16px;">
      <div class="panel-header">
        <div class="panel-title">順位表</div>
        <div class="links">
          <a href="../output/standings.csv">CSV</a>
        </div>
      </div>
      <div id="standingsContent">{first["standingsHtml"]}</div>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">Elo 推移グラフ</div>
          <div class="links">
            <a id="graphLink" href="{html.escape(first["graph"])}">画像を開く</a>
            <a id="tableLink" href="{html.escape(first["tableLink"])}">推移表CSV</a>
          </div>
        </div>
        <div class="graph-wrap">
          <svg class="chart" id="chart" role="img" aria-label="Elo 推移グラフ"></svg>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">最新ランキング</div>
            <div class="links">
              <a id="rankingLink" href="{html.escape(first["rankingLink"])}">CSV</a>
              <a id="latestLink" href="{html.escape(first["latestLink"])}">サマリ</a>
            </div>
          </div>
          <div class="table-wrap" id="rankingTable">{first["rankingHtml"]}</div>
        </div>

        <div class="panel" id="teamLinksPanel" style="display: none;">
          <div class="panel-header">
            <div class="panel-title">球団ページ</div>
          </div>
          <div id="teamLinks"></div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">直近10日 Elo 推移</div>
          </div>
          <div class="table-wrap" id="historyTable">{first["tableHtml"]}</div>
        </div>
      </div>
    </section>
  </main>
  <div class="tooltip" id="tooltip"></div>

  <script>
    const sections = {data_json};
    const teamColors = {colors_json};
    const byKey = new Map(sections.map((item) => [item.key, item]));
    let activeKey = "{first["key"]}";

    const fallbackColors = [
      "#0068b7", "#c43d3d", "#1f8a5b", "#7c3aed", "#d97706", "#475467",
      "#0e7490", "#be123c", "#4d7c0f", "#4338ca", "#a16207", "#525252"
    ];

    function svgEl(name, attrs = {{}}, text = "") {{
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
      if (text) node.textContent = text;
      return node;
    }}

    function teamColor(team, index) {{
      return teamColors[team] || fallbackColors[index % fallbackColors.length];
    }}

    function valueAt(row, team) {{
      const value = row[team];
      if (value === null || value === undefined || value === "") return null;
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }}

    function drawChart(item) {{
      const svg = document.getElementById("chart");
      const tooltip = document.getElementById("tooltip");
      svg.innerHTML = "";

      const rows = item.chartData || [];
      if (!rows.length) {{
        svg.appendChild(svgEl("text", {{ x: "50%", y: "50%", "text-anchor": "middle", fill: "#667085" }}, "データがありません"));
        return;
      }}

      const width = 1120;
      const height = 560;
      const margin = {{ top: 32, right: 24, bottom: 54, left: 56 }};
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);

      const teams = Object.keys(rows[0]).filter((key) => key !== "date");
      const values = [];
      rows.forEach((row) => {{
        teams.forEach((team) => {{
          const value = valueAt(row, team);
          if (value !== null) values.push(value);
        }});
      }});

      const minValue = Math.floor((Math.min(...values) - 15) / 10) * 10;
      const maxValue = Math.ceil((Math.max(...values) + 15) / 10) * 10;
      const x = (index) => margin.left + (rows.length <= 1 ? innerWidth / 2 : (index / (rows.length - 1)) * innerWidth);
      const y = (value) => margin.top + ((maxValue - value) / (maxValue - minValue)) * innerHeight;

      const plot = svgEl("g");
      svg.appendChild(plot);

      for (let i = 0; i <= 5; i += 1) {{
        const value = minValue + ((maxValue - minValue) / 5) * i;
        const yy = y(value);
        plot.appendChild(svgEl("line", {{ x1: margin.left, x2: width - margin.right, y1: yy, y2: yy, stroke: "#1f2937", "stroke-width": 1 }}));
        plot.appendChild(svgEl("text", {{ x: margin.left - 10, y: yy + 4, "text-anchor": "end", fill: "#94a3b8", "font-size": 12 }}, value.toFixed(0)));
      }}

      const dateTickStep = Math.max(1, Math.ceil(rows.length / 8));
      rows.forEach((row, index) => {{
        if (index % dateTickStep !== 0 && index !== rows.length - 1) return;
        const xx = x(index);
        plot.appendChild(svgEl("line", {{ x1: xx, x2: xx, y1: margin.top, y2: height - margin.bottom, stroke: "#151c27", "stroke-width": 1 }}));
        plot.appendChild(svgEl("text", {{ x: xx, y: height - 22, "text-anchor": "middle", fill: "#94a3b8", "font-size": 11 }}, row.date.slice(5)));
      }});

      teams.forEach((team, teamIndex) => {{
        let path = "";
        let started = false;
        rows.forEach((row, rowIndex) => {{
          const value = valueAt(row, team);
          if (value === null) {{
            started = false;
            return;
          }}
          const command = started ? "L" : "M";
          path += `${{command}} ${{x(rowIndex).toFixed(2)}} ${{y(value).toFixed(2)}} `;
          started = true;
        }});
        if (path) {{
          plot.appendChild(svgEl("path", {{
            d: path,
            fill: "none",
            stroke: teamColor(team, teamIndex),
            "stroke-width": 3,
            "stroke-linejoin": "round",
            "stroke-linecap": "round"
          }}));
        }}
      }});

      plot.appendChild(svgEl("line", {{ x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, stroke: "#475569", "stroke-width": 1 }}));
      plot.appendChild(svgEl("line", {{ x1: margin.left, x2: margin.left, y1: margin.top, y2: height - margin.bottom, stroke: "#475569", "stroke-width": 1 }}));

      const cursor = svgEl("line", {{ y1: margin.top, y2: height - margin.bottom, stroke: "#e2e8f0", "stroke-width": 1.5, "stroke-dasharray": "5 4", opacity: 0 }});
      plot.appendChild(cursor);
      const pointLayer = svgEl("g");
      plot.appendChild(pointLayer);
      const hit = svgEl("rect", {{ x: margin.left, y: margin.top, width: innerWidth, height: innerHeight, fill: "transparent" }});
      svg.appendChild(hit);

      function showAt(event) {{
        const rect = svg.getBoundingClientRect();
        const px = ((event.clientX - rect.left) / rect.width) * width;
        const ratio = Math.max(0, Math.min(1, (px - margin.left) / innerWidth));
        const index = Math.round(ratio * (rows.length - 1));
        const row = rows[index];
        const xx = x(index);

        cursor.setAttribute("x1", xx);
        cursor.setAttribute("x2", xx);
        cursor.setAttribute("opacity", "1");
        pointLayer.innerHTML = "";

        const rowsHtml = teams
          .map((team, teamIndex) => [team, valueAt(row, team), teamColor(team, teamIndex)])
          .filter(([, value]) => value !== null)
          .sort((a, b) => b[1] - a[1])
          .map(([team, value, color]) => {{
            pointLayer.appendChild(svgEl("circle", {{ cx: xx, cy: y(value), r: 4.5, fill: color, stroke: "#fff", "stroke-width": 1.5 }}));
            return `<div class="tooltip-row"><span class="swatch" style="background:${{color}}"></span><span>${{team}}</span><strong>${{value.toFixed(1)}}</strong></div>`;
          }})
          .join("");

        tooltip.innerHTML = `<div class="tooltip-title">${{row.date}}</div>${{rowsHtml}}`;
        tooltip.style.display = "block";
        const left = Math.min(window.innerWidth - tooltip.offsetWidth - 12, event.clientX + 14);
        const top = Math.min(window.innerHeight - tooltip.offsetHeight - 12, event.clientY + 14);
        tooltip.style.left = `${{Math.max(12, left)}}px`;
        tooltip.style.top = `${{Math.max(12, top)}}px`;
      }}

      function hide() {{
        cursor.setAttribute("opacity", "0");
        pointLayer.innerHTML = "";
        tooltip.style.display = "none";
      }}

      hit.addEventListener("mousemove", showAt);
      hit.addEventListener("mouseleave", hide);
      hit.addEventListener("touchstart", (event) => showAt(event.touches[0]), {{ passive: true }});
      hit.addEventListener("touchmove", (event) => showAt(event.touches[0]), {{ passive: true }});
    }}

    function setSection(key) {{
      const item = byKey.get(key);
      if (!item) return;
      activeKey = key;

      document.querySelectorAll(".tab").forEach((tab) => {{
        tab.classList.toggle("is-active", tab.dataset.key === key);
      }});

      document.getElementById("pageUpdated").textContent = `更新日時: ${{item.updated}}`;
      document.getElementById("metricLabel").textContent = item.label;
      document.getElementById("metricLatestDate").textContent = item.latestDate;
      document.getElementById("metricGames").textContent = item.games;
      document.getElementById("metricPeriod").textContent = item.period;

      document.getElementById("graphLink").href = item.graph;
      document.getElementById("rankingLink").href = item.rankingLink;
      document.getElementById("tableLink").href = item.tableLink;
      document.getElementById("latestLink").href = item.latestLink;
      document.getElementById("rankingTable").innerHTML = item.rankingHtml;
      document.getElementById("scheduleContent").innerHTML = item.scheduleHtml;
      document.getElementById("standingsContent").innerHTML = item.standingsHtml;
      document.getElementById("historyTable").innerHTML = item.tableHtml;
      document.getElementById("teamLinks").innerHTML = item.teamLinksHtml || "";
      document.getElementById("teamLinksPanel").style.display = item.teamLinksHtml ? "" : "none";
      drawChart(item);
    }}

    document.querySelectorAll(".tab").forEach((tab) => {{
      tab.addEventListener("click", () => setSection(tab.dataset.key));
    }});
    window.addEventListener("resize", () => drawChart(byKey.get(activeKey)));
    drawChart(byKey.get(activeKey));
  </script>
</body>
</html>
"""
