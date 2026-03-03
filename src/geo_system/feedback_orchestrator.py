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
        mention_rate = sum(1 for r in rows if r.mentioned) / len(rows)
        if mention_rate == 0:
            actions.append({
                "priority": "P0",
                "prompt": p.prompt,
                "action": "Create dedicated answer page (definition + FAQ + evidence block).",
            })
        elif mention_rate < 0.4:
            actions.append({
                "priority": "P1",
                "prompt": p.prompt,
                "action": "Strengthen comparison + add data table + schema update.",
            })
    return actions[:20]
