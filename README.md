# GEO System (MVP)

A practical GEO (Generative Engine Optimization) system to help brands become preferred answers in LLM outputs.

## What it does
- Build an intent graph from prompts
- Dedupe and cluster prompts by bucket
- Store and manage GEO assets (entity/faq/comparison/use-case)
- Run model visibility scans (mention/citation/recommendation)
- Support a real OpenAI-compatible scan adapter
- Generate weekly KPI reports with bucket breakdown

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
geo adapter set --provider openai --base-url https://lonr.zeabur.app/v1 --api-key YOUR_KEY --model gpt-5.3-codex
geo adapter set --provider claude --base-url https://api.anthropic.com/v1 --api-key YOUR_KEY --model claude-sonnet-4-6
geo adapter set --provider gemini --base-url https://lonr.zeabur.app/v1 --api-key YOUR_KEY --model gemini-3.1-pro-preview
geo scan run --models openai:live,claude:live,gemini:live --append
geo report weekly
```

## Notes
This MVP stores data locally in JSON files for simplicity.

## v0.3 highlights
- Multi-provider adapter config (openai/claude/gemini)
- Run-level trend comparison (current run vs previous run)
- Action scoring in weekly actions
- Append mode for scan history

## v0.4 highlights
- Bucket-level trend tracking (mention delta per bucket)
- Owner-page mapping CLI (`geo owner set --bucket ... --page ...`)
- Weekly actions now include owner_page suggestions

### Owner-page mapping
```bash
geo owner set --bucket info --page /what-is-tripo3d
geo owner set --bucket comparison --page /tripo3d-vs-meshy
geo owner set --bucket decision --page /best-ai-3d-tools
geo owner set --bucket usecase --page /ai-3d-for-game-assets
```

## v1.0 highlights
- Citation URL extraction and top-cited URL reporting
- Semantic prompt clustering (`prompt_semantic_clusters.json`)
- Content suggestion output (`docs/content_suggestions.json`)
- Better scan data model with cited_urls support

## 🌐 Web Interface (NEW!)

Launch a web interface to easily run GEO scans without CLI:

```bash
# Install Flask
pip install flask

# Start web server
python -m geo_system.web_app
```

Then open http://localhost:5000 in your browser.

### Web Features

1. **Single Scan** - Enter company/product info:
   - Brand name
   - Domain
   - Product description
   - Keywords
   - Select AI models to test

2. **Batch Scan** - Upload JSON config to test multiple companies:
```json
{
  "projects": [
    {"brand": "Tripo3D", "domain": "tripo3d.ai", "keywords": "AI 3D,text to 3D"},
    {"brand": "Meshy", "domain": "meshy.ai", "keywords": "AI 3D,model generation"}
  ],
  "models": "openai:live,claude:live"
}
```

3. **Results Display**:
   - Mention rate, citation rate, recommendation rate
   - Per-model performance breakdown
   - Detailed scan results table

## Dashboard
After running `geo report weekly`, open:

- `dashboard/index.html`

This local HTML dashboard visualizes model KPI, owner-page mappings, weekly actions, and content suggestions.

happy birthday
