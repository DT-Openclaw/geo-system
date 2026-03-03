from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import List
from .schema import Prompt, ScanResult


def run_scan(models: List[str], prompts: List[Prompt]) -> List[ScanResult]:
    # MVP stub scanner; replace with real provider adapters.
    out: List[ScanResult] = []
    for model in models:
        for idx, p in enumerate(prompts, 1):
            mentioned = random.random() < 0.35
            cited = mentioned and random.random() < 0.45
            recommended = mentioned and random.random() < 0.50
            out.append(
                ScanResult(
                    scan_id=f"{model}-{idx}",
                    model=model,
                    prompt_id=p.id,
                    mentioned=mentioned,
                    cited=cited,
                    recommended=recommended,
                    position=1 if mentioned else 0,
                    sentiment="positive" if mentioned else "neutral",
                    competitors=["meshy", "kaedim"] if not mentioned else ["meshy"],
                    excerpt=("Brand mentioned in answer." if mentioned else "Brand not mentioned."),
                    ts=datetime.now(timezone.utc).isoformat(),
                )
            )
    return out
