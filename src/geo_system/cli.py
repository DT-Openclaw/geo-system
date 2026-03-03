from __future__ import annotations
import argparse
from pathlib import Path
from .io_utils import read_json, write_json
from .intent_engine import generate_prompts, dedupe_prompts, cluster_prompts, semantic_cluster_prompts
from .model_testing_engine import run_scan
from .reporting import compute_weekly_kpi, render_weekly_report
from .feedback_orchestrator import suggest_actions
from .schema import Prompt, ScanResult


def _project_paths(base: Path):
    return {
        "prompts": base / "data" / "prompts.json",
        "prompt_clusters": base / "data" / "prompt_clusters.json",
        "prompt_semantic_clusters": base / "data" / "prompt_semantic_clusters.json",
        "scans": base / "data" / "scans.json",
        "kpi": base / "data" / "kpi_weekly.json",
        "report": base / "docs" / "weekly_report.txt",
        "actions": base / "docs" / "weekly_actions.json",
        "content_suggestions": base / "docs" / "content_suggestions.json",
        "adapter": base / "data" / "adapter_config.json",
        "owner_map": base / "data" / "owner_page_map.json",
    }


def cmd_init(args):
    base = Path(args.cwd).resolve()
    (base / "data").mkdir(parents=True, exist_ok=True)
    (base / "docs").mkdir(parents=True, exist_ok=True)
    cfg = {
        "project": args.project,
        "domain": args.domain,
        "brand": args.brand,
        "brand_terms": [args.brand, args.domain],
    }
    write_json(base / "data" / "project.json", cfg)
    print(f"Initialized GEO project at {base}")


def cmd_prompts_generate(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    seeds = [s.strip() for s in args.seed.split(",") if s.strip()]
    prompts_raw = generate_prompts(seeds, args.count)
    prompts = dedupe_prompts(prompts_raw)

    owner_map = read_json(paths["owner_map"], {})
    for p in prompts:
        p.owner_page = owner_map.get(p.bucket, p.owner_page)

    write_json(paths["prompts"], [p.to_dict() for p in prompts])

    clusters = cluster_prompts(prompts)
    cluster_payload = {k: [p.to_dict() for p in v] for k, v in clusters.items()}
    write_json(paths["prompt_clusters"], cluster_payload)

    semantic_clusters = semantic_cluster_prompts(prompts)
    write_json(paths["prompt_semantic_clusters"], semantic_clusters)

    print(f"Generated {len(prompts_raw)} prompts, deduped to {len(prompts)} -> {paths['prompts']}")
    print(f"Clusters -> {paths['prompt_clusters']}")
    print(f"Semantic clusters -> {paths['prompt_semantic_clusters']}")


def cmd_owner_map_set(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    payload = read_json(paths["owner_map"], {})
    payload[args.bucket] = args.page
    write_json(paths["owner_map"], payload)
    print(f"Owner page mapping saved: {args.bucket} -> {args.page}")


def cmd_adapter_set(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    existing = read_json(paths["adapter"], {})

    payload = existing
    payload[args.provider] = {
        "base_url": args.base_url,
        "api_key": args.api_key,
        "model": args.model,
    }
    write_json(paths["adapter"], payload)
    print(f"Adapter config saved for provider={args.provider} -> {paths['adapter']}")


def cmd_scan_run(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    prompts_raw = read_json(paths["prompts"], [])
    prompts = [Prompt(**p) for p in prompts_raw]
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    project = read_json(base / "data" / "project.json", {})
    brand_terms = project.get("brand_terms", [project.get("brand", ""), project.get("domain", "")])

    adapter = read_json(paths["adapter"], {})
    new_scans = [s.to_dict() for s in run_scan(models, prompts, brand_terms=brand_terms, adapter_config=adapter)]

    if args.append:
        existing = read_json(paths["scans"], [])
        scans = existing + new_scans
    else:
        scans = new_scans

    write_json(paths["scans"], scans)
    print(f"Scanned {len(prompts)} prompts x {len(models)} models -> {paths['scans']}")
    print(f"Append mode: {args.append}")


def cmd_report_weekly(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    scans_raw = read_json(paths["scans"], [])
    scans = [ScanResult(**s) for s in scans_raw]

    prompts_raw = read_json(paths["prompts"], [])
    prompts = [Prompt(**p) for p in prompts_raw]

    kpi = compute_weekly_kpi(scans, prompts)
    write_json(paths["kpi"], kpi)
    txt = render_weekly_report(kpi)
    paths["report"].write_text(txt, encoding="utf-8")

    actions = suggest_actions(prompts, scans)
    write_json(paths["actions"], actions)

    content_suggestions = [
        {
            "prompt": a["prompt"],
            "owner_page": a["owner_page"],
            "suggestion": a["action"],
            "priority": a["priority"],
            "score": a["score"],
        }
        for a in actions[:10]
    ]
    write_json(paths["content_suggestions"], content_suggestions)

    print(f"Weekly report -> {paths['report']}")
    print(f"Actions -> {paths['actions']}")
    print(f"Content suggestions -> {paths['content_suggestions']}")


def main():
    parser = argparse.ArgumentParser(prog="geo")
    parser.add_argument("--cwd", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--project", required=True)
    p_init.add_argument("--domain", required=True)
    p_init.add_argument("--brand", required=True)
    p_init.set_defaults(func=cmd_init)

    p_prompts = sub.add_parser("prompts")
    sub_prompts = p_prompts.add_subparsers(dest="prompts_cmd", required=True)
    p_generate = sub_prompts.add_parser("generate")
    p_generate.add_argument("--seed", required=True, help="comma separated seed terms")
    p_generate.add_argument("--count", type=int, default=100)
    p_generate.set_defaults(func=cmd_prompts_generate)

    p_owner = sub.add_parser("owner")
    sub_owner = p_owner.add_subparsers(dest="owner_cmd", required=True)
    p_owner_set = sub_owner.add_parser("set")
    p_owner_set.add_argument("--bucket", required=True, choices=["info", "comparison", "decision", "usecase"])
    p_owner_set.add_argument("--page", required=True)
    p_owner_set.set_defaults(func=cmd_owner_map_set)

    p_adapter = sub.add_parser("adapter")
    sub_adapter = p_adapter.add_subparsers(dest="adapter_cmd", required=True)
    p_adapter_set = sub_adapter.add_parser("set")
    p_adapter_set.add_argument("--provider", required=True, choices=["openai", "claude", "gemini"])
    p_adapter_set.add_argument("--base-url", required=True)
    p_adapter_set.add_argument("--api-key", required=True)
    p_adapter_set.add_argument("--model", required=True)
    p_adapter_set.set_defaults(func=cmd_adapter_set)

    p_scan = sub.add_parser("scan")
    sub_scan = p_scan.add_subparsers(dest="scan_cmd", required=True)
    p_run = sub_scan.add_parser("run")
    p_run.add_argument("--models", default="gpt,claude,gemini")
    p_run.add_argument("--append", action="store_true")
    p_run.set_defaults(func=cmd_scan_run)

    p_report = sub.add_parser("report")
    sub_report = p_report.add_subparsers(dest="report_cmd", required=True)
    p_weekly = sub_report.add_parser("weekly")
    p_weekly.set_defaults(func=cmd_report_weekly)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
