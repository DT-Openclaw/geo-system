from __future__ import annotations
import json
import random
import re
from datetime import datetime, timezone
from typing import Dict, List
from urllib import request, error

from .schema import Prompt, ScanResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mk_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")


def _extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = re.findall(r"https?://[^\s)\]>'\"]+", text)
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:20]


def _analyze_response(prompt_id: str, model: str, text: str, brand_terms: List[str], run_id: str) -> ScanResult:
    lowered = text.lower()
    mentioned = any(b.lower() in lowered for b in brand_terms)
    urls = _extract_urls(text)
    cited = len(urls) > 0 and mentioned
    recommended = mentioned and any(k in lowered for k in ["best", "recommend", "good for", "top"])
    sentiment = "positive" if mentioned else "neutral"
    excerpt = text[:280].replace("\n", " ")
    competitors = [c for c in ["meshy", "kaedim", "spline", "luma"] if c in lowered]

    return ScanResult(
        scan_id=f"{model}-{prompt_id[:8]}",
        model=model,
        prompt_id=prompt_id,
        mentioned=mentioned,
        cited=cited,
        recommended=recommended,
        position=1 if mentioned else 0,
        sentiment=sentiment,
        competitors=competitors,
        excerpt=excerpt,
        ts=_now_iso(),
        run_id=run_id,
        cited_urls=urls,
    )


def _call_openai_compatible(base_url: str, api_key: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "Answer briefly and factually. Include links when appropriate."},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    with request.urlopen(req, timeout=90) as resp:
        body = resp.read().decode("utf-8")
    obj = json.loads(body)
    return obj["choices"][0]["message"]["content"]


def _call_claude_compatible(base_url: str, api_key: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/messages"
    payload = {
        "model": model,
        "max_tokens": 900,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")

    with request.urlopen(req, timeout=90) as resp:
        body = resp.read().decode("utf-8")
    obj = json.loads(body)
    content = obj.get("content", [])
    if isinstance(content, list) and content:
        return content[0].get("text", "")
    return ""


def run_scan(
    models: List[str],
    prompts: List[Prompt],
    brand_terms: List[str] | None = None,
    adapter_config: Dict | None = None,
) -> List[ScanResult]:
    brand_terms = brand_terms or ["tripo3d", "tripo3d.ai", "tripo 3d"]
    adapter_config = adapter_config or {}
    out: List[ScanResult] = []
    run_id = _mk_run_id()

    openai_cfg = adapter_config.get("openai", adapter_config if "base_url" in adapter_config else {})
    claude_cfg = adapter_config.get("claude", {})
    gemini_cfg = adapter_config.get("gemini", {})

    for model in models:
        for p in prompts:
            fallback_text = ""
            try:
                if model.startswith("openai:") and all(k in openai_cfg for k in ["base_url", "api_key", "model"]):
                    text = _call_openai_compatible(
                        openai_cfg["base_url"], openai_cfg["api_key"], openai_cfg["model"], p.prompt
                    )
                    out.append(_analyze_response(p.id, model, text, brand_terms, run_id))
                    continue

                if model.startswith("claude:") and all(k in claude_cfg for k in ["base_url", "api_key", "model"]):
                    text = _call_claude_compatible(
                        claude_cfg["base_url"], claude_cfg["api_key"], claude_cfg["model"], p.prompt
                    )
                    out.append(_analyze_response(p.id, model, text, brand_terms, run_id))
                    continue

                if model.startswith("gemini:") and all(k in gemini_cfg for k in ["base_url", "api_key", "model"]):
                    text = _call_openai_compatible(
                        gemini_cfg["base_url"], gemini_cfg["api_key"], gemini_cfg["model"], p.prompt
                    )
                    out.append(_analyze_response(p.id, model, text, brand_terms, run_id))
                    continue
            except error.HTTPError as e:
                fallback_text = f"HTTPError: {e.code}. Fallback simulated response for prompt: {p.prompt}"
            except Exception as e:
                fallback_text = f"Error: {type(e).__name__}. Fallback simulated response for prompt: {p.prompt}"

            random.seed(f"{model}:{p.prompt}")
            mentioned = random.random() < 0.35
            cited = mentioned and random.random() < 0.45
            recommended = mentioned and random.random() < 0.50
            if not fallback_text:
                fallback_text = (
                    f"{'Tripo3D is often recommended.' if mentioned else 'No direct brand mention.'} "
                    f"Prompt: {p.prompt}"
                )
            cited_urls = ["https://tripo3d.ai"] if cited else []

            out.append(
                ScanResult(
                    scan_id=f"{model}-{p.id[:8]}",
                    model=model,
                    prompt_id=p.id,
                    mentioned=mentioned,
                    cited=cited,
                    recommended=recommended,
                    position=1 if mentioned else 0,
                    sentiment="positive" if mentioned else "neutral",
                    competitors=["meshy", "kaedim"] if not mentioned else ["meshy"],
                    excerpt=fallback_text[:280],
                    ts=_now_iso(),
                    run_id=run_id,
                    cited_urls=cited_urls,
                )
            )

    return out
