from __future__ import annotations
import uuid
from typing import List
from .schema import Prompt


def _bucket_for_prompt(text: str) -> str:
    t = text.lower()
    if "vs" in t or "alternative" in t:
        return "comparison"
    if "best" in t or "which" in t:
        return "decision"
    if "what is" in t or "how" in t or "why" in t:
        return "info"
    return "usecase"


def generate_prompts(seed_terms: List[str], count: int = 100) -> List[Prompt]:
    templates = [
        "What is {x}?",
        "How does {x} work?",
        "Why use {x}?",
        "Best tools for {x}",
        "{x} alternatives",
        "{x} vs competitors",
        "Is {x} good for game assets?",
        "Is {x} good for e-commerce?",
        "Which AI can do {x}?",
        "How to choose {x} tools?",
    ]

    prompts: List[Prompt] = []
    i = 0
    while len(prompts) < count:
        term = seed_terms[i % len(seed_terms)].strip()
        tpl = templates[i % len(templates)]
        text = tpl.format(x=term)
        bucket = _bucket_for_prompt(text)
        prompts.append(
            Prompt(
                id=str(uuid.uuid4()),
                prompt=text,
                bucket=bucket,
                intent_type=bucket,
                stage="awareness" if bucket == "info" else "consideration",
                priority="P0" if len(prompts) < 30 else "P1",
            )
        )
        i += 1
    return prompts
