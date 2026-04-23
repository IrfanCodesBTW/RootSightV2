# RootSight V3

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-4285F4?style=flat&logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**RootSight V3** is a zero-infrastructure AI incident intelligence engine designed for evidence-based root cause analysis (RCA). It reconstructs factual incident timelines from logs, generates evidence-backed hypotheses, and retrieves similar past incidents to accelerate resolution.

---

## 🚀 Key Features

- **Automated Timeline Reconstruction**: Chronological reconstruction of events from raw logs using LLMs.
- **Evidence-Based RCA**: Ranked hypotheses with supporting evidence and confidence scores.
- **Memory Retrieval**: Uses FAISS for local vector storage to find similar historical incidents.
- **Automated Recovery Scripts**: Drafts safe, idempotent bash recovery scripts based on RCA to accelerate incident mitigation.
- **Zero-Cost AI**: Designed to operate within free-tier limits of Gemini and Groq.
- **Operational Dashboard**: Modern, high-performance UI built with Next.js and Framer Motion.

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
