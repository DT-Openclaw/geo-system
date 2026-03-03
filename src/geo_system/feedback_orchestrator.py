from __future__ import annotations
from typing import List, Dict
from .schema import Prompt, ScanResult


def suggest_actions(prompts: List[Prompt], scans: List[ScanResult]) -> List[Dict]:
    scan_by_prompt = {}
    for s in scans:
        key = s.prompt_id
        if key not in scan_by_prompt:
            scan_by_prompt[key] = []
        scan_by_prompt[key].append(s)

    actions = []
    for p in prompts:
        rows = scan_by_prompt.get(p.id, [])
        if not rows:
            continue
        total = len(rows)
        mention_rate = sum(1 for r in rows if r.mentioned) / total
        citation_rate = sum(1 for r in rows if r.cited) / total
        recommendation_rate = sum(1 for r in rows if r.recommended) / total

        if mention_rate == 0:
            score = 100
            action = "Create dedicated answer page (definition + FAQ + evidence block)."
            reason = "Zero mentions across runs"
            priority = "P0"
        elif mention_rate < 0.4 and citation_rate == 0:
            score = 85
            action = "Strengthen comparison + add data table + schema update."
            reason = "Weak mentions and no citations"
            priority = "P1"
        elif recommendation_rate == 0 and mention_rate > 0:
            score = 70
            action = "Add 'best for' / 'who it is for' / alternative comparison blocks."
            reason = "Mentioned but not recommended"
            priority = "P1"
        else:
            score = 50
            action = "Refresh facts, benchmark blocks, and last-updated signals."
            reason = "Needs incremental authority improvements"
            priority = "P2"

        actions.append({
            "priority": priority,
            "score": score,
            "prompt": p.prompt,
            "bucket": p.bucket,
            "mention_rate": round(mention_rate, 4),
            "citation_rate": round(citation_rate, 4),
            "recommendation_rate": round(recommendation_rate, 4),
            "reason": reason,
            "action": action,
        })

    actions.sort(key=lambda x: (-x["score"], x["priority"], x["prompt"]))
    return actions[:20]
