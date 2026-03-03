# GEO System (MVP)

A practical GEO (Generative Engine Optimization) system to help brands become preferred answers in LLM outputs.

## What it does (MVP)
- Build an intent graph from prompts
- Store and manage GEO assets (entity/faq/comparison/use-case)
- Run model visibility scans (mention/citation/recommendation)
- Generate weekly KPI reports

## Architecture
- `src/geo_system/intent_engine.py`
- `src/geo_system/content_engine.py`
- `src/geo_system/model_testing_engine.py`
- `src/geo_system/feedback_orchestrator.py`
- `src/geo_system/reporting.py`

## Quick start
```bash
cd geo-system
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

geo init --project tripo3d --domain tripo3d.ai --brand tripo3d
geo prompts generate --seed "3d,ai 3d,text to 3d,image to 3d" --count 100
geo scan run --models gpt,claude,gemini
geo report weekly
```

## Notes
This MVP stores data locally in JSON files for simplicity.
