from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List

from .io_utils import read_json


def build_dashboard_payload(base: Path) -> Dict:
    data_dir = base / "data"
    docs_dir = base / "docs"
    payload = {
        "project": read_json(data_dir / "project.json", {}),
        "kpi": read_json(data_dir / "kpi_weekly.json", {}),
        "actions": read_json(docs_dir / "weekly_actions.json", []),
        "content_suggestions": read_json(docs_dir / "content_suggestions.json", []),
        "owner_page_map": read_json(data_dir / "owner_page_map.json", {}),
    }
    return payload


def render_dashboard_html(payload: Dict) -> str:
    blob = json.dumps(payload, ensure_ascii=False)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GEO Dashboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; background: #0b1020; color: #eef2ff; }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .card {{ background: #131a2e; border: 1px solid #26304f; border-radius: 12px; padding: 16px; }}
    h1,h2,h3 {{ margin: 0 0 12px 0; }}
    .muted {{ color: #9fb0d0; font-size: 14px; }}
    .stat {{ font-size: 28px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid #243150; text-align: left; vertical-align: top; }}
    th {{ color: #9fb0d0; font-weight: 600; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #1d2a47; color: #c9d6ff; font-size: 12px; }}
    .good {{ color: #7ee787; }} .warn {{ color: #f2cc60; }} .bad {{ color: #ff7b72; }}
    .two {{ display:grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    a {{ color: #8ab4ff; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>GEO Dashboard</h1>
    <div class="muted" id="project"></div>

    <div class="grid" id="summary"></div>

    <div class="two" style="margin-top:16px;">
      <div class="card">
        <h2>Model KPI</h2>
        <div id="models"></div>
      </div>
      <div class="card">
        <h2>Owner Page Map</h2>
        <div id="ownerMap"></div>
      </div>
    </div>

    <div class="card" style="margin-top:16px;">
      <h2>Prioritized Weekly Actions</h2>
      <div id="actions"></div>
    </div>

    <div class="card" style="margin-top:16px;">
      <h2>Content Suggestions</h2>
      <div id="suggestions"></div>
    </div>
  </div>

<script>
const DATA = {blob};

function pct(n) {{ return ((n || 0) * 100).toFixed(1) + '%'; }}
function esc(s) {{ return String(s ?? '').replace(/[&<>\"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c])); }}

const project = DATA.project || {{}};
document.getElementById('project').innerHTML = `${{esc(project.project || 'unknown')}} · domain: ${{esc(project.domain || '-')}} · brand: ${{esc(project.brand || '-')}}`;

const models = DATA.kpi?.models || {{}};
const summary = document.getElementById('summary');
Object.entries(models).forEach(([model, row]) => {{
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <h3>${{esc(model)}}</h3>
    <div class="muted">total prompts</div>
    <div class="stat">${{row.total ?? 0}}</div>
    <div class="muted">mention ${{pct(row.mention_rate)}} · citation ${{pct(row.citation_rate)}} · recommendation ${{pct(row.recommendation_rate)}}</div>
  `;
  summary.appendChild(card);
}});

const modelsDiv = document.getElementById('models');
let modelHtml = '<table><thead><tr><th>Model</th><th>Mention</th><th>Citation</th><th>Recommendation</th></tr></thead><tbody>';
for (const [model, row] of Object.entries(models)) {{
  modelHtml += `<tr><td>${{esc(model)}}</td><td>${{pct(row.mention_rate)}}</td><td>${{pct(row.citation_rate)}}</td><td>${{pct(row.recommendation_rate)}}</td></tr>`;
}}
modelHtml += '</tbody></table>';
modelsDiv.innerHTML = modelHtml;

const ownerMap = document.getElementById('ownerMap');
const om = DATA.owner_page_map || {{}};
ownerMap.innerHTML = '<table><thead><tr><th>Bucket</th><th>Owner Page</th></tr></thead><tbody>' +
  Object.entries(om).map(([k,v]) => `<tr><td><span class="pill">${{esc(k)}}</span></td><td>${{esc(v)}}</td></tr>`).join('') + '</tbody></table>';

const actions = document.getElementById('actions');
const rows = (DATA.actions || []).slice(0, 12);
actions.innerHTML = '<table><thead><tr><th>Priority</th><th>Score</th><th>Prompt</th><th>Owner Page</th><th>Action</th></tr></thead><tbody>' +
  rows.map(r => `<tr><td>${{esc(r.priority)}}</td><td>${{esc(r.score)}}</td><td>${{esc(r.prompt)}}</td><td>${{esc(r.owner_page)}}</td><td>${{esc(r.action)}}</td></tr>`).join('') + '</tbody></table>';

const sugg = document.getElementById('suggestions');
const srows = (DATA.content_suggestions || []).slice(0, 12);
sugg.innerHTML = '<table><thead><tr><th>Priority</th><th>Score</th><th>Prompt</th><th>Owner Page</th><th>Suggestion</th></tr></thead><tbody>' +
  srows.map(r => `<tr><td>${{esc(r.priority)}}</td><td>${{esc(r.score)}}</td><td>${{esc(r.prompt)}}</td><td>${{esc(r.owner_page)}}</td><td>${{esc(r.suggestion)}}</td></tr>`).join('') + '</tbody></table>';
</script>
</body>
</html>'''


def build_dashboard_files(base: Path) -> Dict[str, str]:
    dashboard_dir = base / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload(base)
    payload_path = dashboard_dir / "dashboard_data.json"
    html_path = dashboard_dir / "index.html"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_dashboard_html(payload), encoding="utf-8")
    return {"json": str(payload_path), "html": str(html_path)}
