from __future__ import annotations
import argparse
from pathlib import Path
from .io_utils import read_json, write_json
from .intent_engine import generate_prompts
from .model_testing_engine import run_scan
from .reporting import compute_weekly_kpi, render_weekly_report
from .feedback_orchestrator import suggest_actions
from .schema import Prompt, ScanResult


def _project_paths(base: Path):
    return {
        "prompts": base / "data" / "prompts.json",
        "scans": base / "data" / "scans.json",
        "kpi": base / "data" / "kpi_weekly.json",
        "report": base / "docs" / "weekly_report.txt",
        "actions": base / "docs" / "weekly_actions.json",
    }


def cmd_init(args):
    base = Path(args.cwd).resolve()
    (base / "data").mkdir(parents=True, exist_ok=True)
    (base / "docs").mkdir(parents=True, exist_ok=True)
    cfg = {
        "project": args.project,
        "domain": args.domain,
        "brand": args.brand,
    }
    write_json(base / "data" / "project.json", cfg)
    print(f"Initialized GEO project at {base}")


def cmd_prompts_generate(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    seeds = [s.strip() for s in args.seed.split(",") if s.strip()]
    prompts = [p.to_dict() for p in generate_prompts(seeds, args.count)]
    write_json(paths["prompts"], prompts)
    print(f"Generated {len(prompts)} prompts -> {paths['prompts']}")


def cmd_scan_run(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    prompts_raw = read_json(paths["prompts"], [])
    prompts = [Prompt(**p) for p in prompts_raw]
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    scans = [s.to_dict() for s in run_scan(models, prompts)]
    write_json(paths["scans"], scans)
    print(f"Scanned {len(prompts)} prompts x {len(models)} models -> {paths['scans']}")


def cmd_report_weekly(args):
    base = Path(args.cwd).resolve()
    paths = _project_paths(base)
    scans_raw = read_json(paths["scans"], [])
    scans = [ScanResult(**s) for s in scans_raw]
    kpi = compute_weekly_kpi(scans)
    write_json(paths["kpi"], kpi)
    txt = render_weekly_report(kpi)
    paths["report"].write_text(txt, encoding="utf-8")

    prompts_raw = read_json(paths["prompts"], [])
    prompts = [Prompt(**p) for p in prompts_raw]
    actions = suggest_actions(prompts, scans)
    write_json(paths["actions"], actions)

    print(f"Weekly report -> {paths['report']}")
    print(f"Actions -> {paths['actions']}")


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

    p_scan = sub.add_parser("scan")
    sub_scan = p_scan.add_subparsers(dest="scan_cmd", required=True)
    p_run = sub_scan.add_parser("run")
    p_run.add_argument("--models", default="gpt,claude,gemini")
    p_run.set_defaults(func=cmd_scan_run)

    p_report = sub.add_parser("report")
    sub_report = p_report.add_subparsers(dest="report_cmd", required=True)
    p_weekly = sub_report.add_parser("weekly")
    p_weekly.set_defaults(func=cmd_report_weekly)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
