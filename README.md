# RootSight V3

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-4285F4?style=flat&logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**From P0 alert to evidence-backed RCA in four minutes, not hours.**

## 📖 Product Overview
RootSight is an AI-powered incident intelligence engine designed to automate the analytical heavy lifting of Site Reliability Engineering. The platform orchestrates a multi-stage pipeline—integrating log ingestion, event extraction, and timeline compression—to transform raw alert payloads from PagerDuty and Datadog into factual incident narratives. By replacing manual log interrogation with automated event reconstruction, RootSight provides SREs with a clear starting point for remediation within minutes of an alert firing.

The system is built on an asynchronous FastAPI backend and a Next.js interface optimized for rapid decision-making. At its core, RootSight utilizes a local vectorized memory store to surface historical context, matching current failures against a library of past incidents and their verified resolutions. This evidence-anchored approach generates ranked RCA hypotheses and idempotent recovery scripts, ensuring that on-call engineers receive actionable intelligence grounded in concrete system behavior rather than high-level summaries.

## 🚀 Why RootSight
- **Automated Timeline Reconstruction:** Condenses thousands of raw log lines into a factual, chronological sequence of events with >80% accuracy in under 60 seconds.
- **Evidence-Anchored Hypotheses:** Surfaces ranked RCA leads with direct log citations and confidence scores, eliminating diagnostic guesswork during high-pressure outages.
- **Deterministic Action Generation:** Produces clear recommended remediation steps and recovery scripts grounded in historical incident memory and real-time system state.

## ⚖️ Technical Differentiation
RootSight differs from orchestration tools like Rootly or PagerDuty AI by operating as a deep-reasoning layer rather than a workflow manager. While traditional tools focus on incident communication and status updates, RootSight performs surgical evidence extraction from sampled logs to build a verifiable chain of causality. Its local-first vector architecture allows teams to maintain a persistent memory of failure modes and fixes without the cost or security risks of large-scale log retention, delivering a faster, data-backed path to root cause identification.


---

## 📂 Project Structure

```text
RootSightV3/
├── src/                    # All source code
│   ├── app/                # Next.js App Router (Frontend)
│   ├── components/         # Reusable UI components
│   ├── features/           # Backend modules (action, impact, rca, etc.)
│   ├── lib/                # Frontend API clients and shared logic
│   ├── schemas/            # Unified data models (Pydantic + TypeScript)
│   ├── utils/              # Backend utility functions
│   └── main.py             # FastAPI backend entry point
├── public/                 # Static assets
├── config/                 # Configuration and environment templates
├── tests/                  # Test suites for backend and frontend
├── docs/                   # Product documentation and guides
├── scripts/                # Maintenance scripts
├── pyproject.toml          # Python dependencies (managed by uv)
├── package.json            # Frontend dependencies
└── README.md               # You are here
```

---

## 🛠️ Getting Started

### Prerequisites

- **Python 3.11+**: Managed via [uv](https://github.com/astral-sh/uv).
- **Node.js 18+**: For the frontend dashboard.
- **API Keys**: Google Gemini API key (for reasoning) and Groq API key (for fast formatting).

### 1. Environment Configuration

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

### 2. Backend Setup

```bash
uv sync
uv run uvicorn src.main:app --reload
```

### 3. Frontend Setup

```bash
npm install
npm run dev
```

Visit `http://localhost:3000` to access the dashboard.

---

## 📖 Documentation

- [PRD](docs/PRD.md): Product requirements and roadmap.
- [Architecture](docs/ARCHITECTURE.md): Technical deep-dive into the pipeline.
- [Contributing](CONTRIBUTING.md): How to get involved.

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
