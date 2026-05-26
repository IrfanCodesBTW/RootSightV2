# 🔍 RootSight

**AI-Powered Incident Understanding & Action System**

Recho "# RootSight" >> README.md



---

## What It Does

| Step | Manual (Today) | With RootSight |
|---|---|---|
| Timeline reconstruction | 15–30 min across 5 tabs | **Automated** — structured timeline in seconds |
| Root cause analysis | Guesswork + pattern recognition | **Evidence-backed** hypotheses with confidence scores |
| Impact assessment | Incomplete mental estimates | **Quantified** blast radius and severity |
| Historical pattern matching | "I think we saw this before..." | **Vector search** across past incidents |
| Follow-up actions | Write Jira + Slack from scratch | **Auto-drafted** tickets and messages |

## Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Setup

```bash
# Clone and enter the project
cd RootSight

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Run the Demo

```bash
# Build the memory index (first time only)
python scripts/build_memory_index.py

# Launch the Streamlit UI
python -m uvicorn app:app --port 8000
```

### Run Tests

```bash
pytest tests/ -v
```

## Architecture

RootSight uses a multi-agent pipeline where each agent owns one responsibility:

```
Alert → Trigger → Log → Timeline → RCA → Impact → Memory → Action → Brief
```

Each agent produces schema-validated output that flows to the next. If any agent fails, the pipeline continues with degraded confidence.

See [architecture.md](architecture.md) for full details.

## Project Structure

```
src/
├── schemas/          # Pydantic data models
├── agents/           # Pipeline agents (trigger, log, timeline, rca, impact, memory, action, manager)
├── prompts/          # LLM prompt templates
├── integrations/     # External API clients (Gemini, Datadog, PagerDuty)
├── services/         # Business logic (normalizer, vector store, persistence)
└── utils/            # Helpers (logging)

data/                 # Seed data, mock responses, incident storage
```

## License

MIT
