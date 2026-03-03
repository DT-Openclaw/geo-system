from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
from .schema import Prompt, ScanResult


def _safe_rate(n: int, d: int) -> float:
    return round((n / d), 4) if d else 0.0


def compute_weekly_kpi(scans: List[ScanResult], prompts: List[Prompt] | None = None) -> Dict:
    prompts = prompts or []
    prompt_by_id = {p.id: p for p in prompts}

    by_model = defaultdict(list)
    by_bucket = defaultdict(list)
    by_model_run = defaultdict(lambda: defaultdict(list))

    for s in scans:
        by_model[s.model].append(s)
        by_model_run[s.model][s.run_id or "no_run_id"].append(s)
        bucket = prompt_by_id.get(s.prompt_id).bucket if s.prompt_id in prompt_by_id else "unknown"
        by_bucket[(s.model, bucket)].append(s)

    model_rows = {}
    for m, rows in by_model.items():
        total = len(rows)
        mention = sum(1 for r in rows if r.mentioned)
        citation = sum(1 for r in rows if r.cited)
        rec = sum(1 for r in rows if r.recommended)
        model_rows[m] = {
            "total": total,
            "mention_rate": _safe_rate(mention, total),
            "citation_rate": _safe_rate(citation, total),
            "recommendation_rate": _safe_rate(rec, total),
        }

    bucket_rows = {}
    for (model, bucket), rows in by_bucket.items():
        total = len(rows)
        mention = sum(1 for r in rows if r.mentioned)
        citation = sum(1 for r in rows if r.cited)
        rec = sum(1 for r in rows if r.recommended)
        bucket_rows.setdefault(model, {})[bucket] = {
            "total": total,
            "mention_rate": _safe_rate(mention, total),
            "citation_rate": _safe_rate(citation, total),
            "recommendation_rate": _safe_rate(rec, total),
        }

    trends = {}
    for model, run_map in by_model_run.items():
        run_ids = sorted(run_map.keys())
        if len(run_ids) < 2:
            continue
        prev_rows = run_map[run_ids[-2]]
        cur_rows = run_map[run_ids[-1]]

        prev_total = len(prev_rows)
        cur_total = len(cur_rows)
        prev_m = _safe_rate(sum(1 for r in prev_rows if r.mentioned), prev_total)
        cur_m = _safe_rate(sum(1 for r in cur_rows if r.mentioned), cur_total)
        prev_c = _safe_rate(sum(1 for r in prev_rows if r.cited), prev_total)
        cur_c = _safe_rate(sum(1 for r in cur_rows if r.cited), cur_total)
        prev_r = _safe_rate(sum(1 for r in prev_rows if r.recommended), prev_total)
        cur_r = _safe_rate(sum(1 for r in cur_rows if r.recommended), cur_total)

        trends[model] = {
            "prev_run_id": run_ids[-2],
            "cur_run_id": run_ids[-1],
            "mention_rate_prev": prev_m,
            "mention_rate_cur": cur_m,
            "mention_delta": round(cur_m - prev_m, 4),
            "citation_rate_prev": prev_c,
            "citation_rate_cur": cur_c,
            "citation_delta": round(cur_c - prev_c, 4),
            "recommendation_rate_prev": prev_r,
            "recommendation_rate_cur": cur_r,
            "recommendation_delta": round(cur_r - prev_r, 4),
        }

    return {"models": model_rows, "by_bucket": bucket_rows, "trends": trends}


def render_weekly_report(kpi: Dict) -> str:
    lines = ["GEO Weekly Report", "=" * 60, ""]
    for model, row in kpi.get("models", {}).items():
        lines.append(f"Model: {model}")
        lines.append(f"- Total prompts: {row['total']}")
        lines.append(f"- Mention rate: {row['mention_rate']*100:.1f}%")
        lines.append(f"- Citation rate: {row['citation_rate']*100:.1f}%")
        lines.append(f"- Recommendation rate: {row['recommendation_rate']*100:.1f}%")
        lines.append("")

        if model in kpi.get("by_bucket", {}):
            lines.append("  By bucket:")
            for bucket, brow in sorted(kpi["by_bucket"][model].items()):
                lines.append(
                    f"  - {bucket}: mention {brow['mention_rate']*100:.1f}% | "
                    f"citation {brow['citation_rate']*100:.1f}% | "
                    f"recommendation {brow['recommendation_rate']*100:.1f}%"
                )
            lines.append("")

        t = kpi.get("trends", {}).get(model)
        if t:
            lines.append("  Trend vs previous run:")
            lines.append(
                f"  - Mention: {t['mention_rate_prev']*100:.1f}% -> {t['mention_rate_cur']*100:.1f}% "
                f"(delta {t['mention_delta']*100:+.1f}pp)"
            )
            lines.append(
                f"  - Citation: {t['citation_rate_prev']*100:.1f}% -> {t['citation_rate_cur']*100:.1f}% "
                f"(delta {t['citation_delta']*100:+.1f}pp)"
            )
            lines.append(
                f"  - Recommendation: {t['recommendation_rate_prev']*100:.1f}% -> {t['recommendation_rate_cur']*100:.1f}% "
                f"(delta {t['recommendation_delta']*100:+.1f}pp)"
            )
            lines.append("")

    return "\n".join(lines)
