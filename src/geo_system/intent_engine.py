from __future__ import annotations
import re
import uuid
from collections import defaultdict
from typing import Dict, List, Tuple
from .schema import Prompt


STOPWORDS = {
    "what", "is", "how", "does", "why", "use", "best", "tools", "for", "which", "ai",
    "good", "to", "do", "the", "a", "an", "of", "and", "in", "on", "with", "vs",
}


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _bucket_for_prompt(text: str) -> str:
    t = text.lower()
    if "vs" in t or "alternative" in t or "compare" in t:
        return "comparison"
    if any(k in t for k in ["best", "which", "top", "recommend"]):
        return "decision"
    if any(k in t for k in ["what is", "how", "why", "guide", "explain"]):
        return "info"
    if any(k in t for k in ["for ", "use case", "workflow"]):
        return "usecase"
    return "info"


def _tokenize(text: str) -> List[str]:
    parts = re.findall(r"[a-z0-9]+", text.lower())
    return [p for p in parts if p not in STOPWORDS]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


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


def dedupe_prompts(prompts: List[Prompt]) -> List[Prompt]:
    seen = set()
    out: List[Prompt] = []
    for p in prompts:
        key = _normalize(p.prompt)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def cluster_prompts(prompts: List[Prompt]) -> Dict[str, List[Prompt]]:
    clusters: Dict[str, List[Prompt]] = defaultdict(list)
    for p in prompts:
        clusters[p.bucket].append(p)
    return dict(clusters)


def semantic_cluster_prompts(prompts: List[Prompt], threshold: float = 0.5) -> Dict[str, List[str]]:
    groups: List[Tuple[str, List[str], List[str]]] = []  # (anchor_id, tokens, prompt_ids)
    for p in prompts:
        toks = _tokenize(p.prompt)
        placed = False
        for idx, (anchor_id, anchor_toks, prompt_ids) in enumerate(groups):
            if _jaccard(toks, anchor_toks) >= threshold:
                prompt_ids.append(p.id)
                placed = True
                break
        if not placed:
            groups.append((p.id, toks, [p.id]))

    return {anchor_id: prompt_ids for anchor_id, _, prompt_ids in groups}
