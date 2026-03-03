from __future__ import annotations
from collections import defaultdict
from typing import List, Dict
from .schema import ScanResult


def compute_weekly_kpi(scans: List[ScanResult]) -> Dict:
    by_model = defaultdict(list)
    for s in scans:
        by_model[s.model].append(s)

    model_rows = {}
    for m, rows in by_model.items():
        total = len(rows) or 1
        mention = sum(1 for r in rows if r.mentioned)
        citation = sum(1 for r in rows if r.cited)
        rec = sum(1 for r in rows if r.recommended)
        model_rows[m] = {
            "total": total,
            "mention_rate": round(mention / total, 4),
            "citation_rate": round(citation / total, 4),
            "recommendation_rate": round(rec / total, 4),
        }

    return {"models": model_rows}


def render_weekly_report(kpi: Dict) -> str:
    lines = ["GEO Weekly Report", "=" * 40, ""]
    for model, row in kpi.get("models", {}).items():
        lines.append(f"Model: {model}")
        lines.append(f"- Total prompts: {row['total']}")
        lines.append(f"- Mention rate: {row['mention_rate']*100:.1f}%")
        lines.append(f"- Citation rate: {row['citation_rate']*100:.1f}%")
        lines.append(f"- Recommendation rate: {row['recommendation_rate']*100:.1f}%")
        lines.append("")
    return "\n".join(lines)
