# RootSight: Product Requirements Document (PRD)

## 1. Product Overview
**Name:** RootSight  
**One-Liner:** Zero-infrastructure AI incident intelligence engine for evidence-based root cause analysis.  
**Category:** AIOps / Incident Management / Reliability Engineering.

---

## 2. Problem Statement
Incident response is currently bogged down by:
- **Alert Fatigue:** High volume of logs and alerts without context.
- **Context Fragmentation:** Logs in Datadog, alerts in PagerDuty, and history in Jira are disconnected.
- **The "RCA Tax":** Writing post-mortems is manual, slow, and often lacks concrete evidence.
- **Costly AI:** Existing AIOps tools are expensive enterprise solutions.

---

## 3. Product Vision
To provide every engineering team with enterprise-grade incident intelligence that runs for free, reconstructs timelines with evidence, and automates the manual labor of RCA and communication.

---

## 4. Goals & Non-Goals

### Goals
- Reconstruct a factual incident timeline from sampled logs with >80% accuracy.
- Generate at least 2 evidence-backed RCA hypotheses within 60 seconds of a trigger.
- Maintain zero AI cost by using free-tier API limits (Gemini/Groq).
- Enable "one-click" drafting for Jira and Slack.

### Non-Goals
- **Auto-Remediation:** RootSight will NEVER execute code to fix an issue.
- **Full Log Retention:** RootSight is an intelligence layer, not a log aggregator.
- **Predictive Analytics:** We focus on active incidents, not "predicting" future ones.

---

## 5. Target Users

| User | Context | Main Need |
| :--- | :--- | :--- |
| **On-call Engineer** | Active outage, high stress. | Immediate, evidence-backed "what happened" summary. |
| **Engineering Manager** | Post-incident review. | Accurate timeline and draft RCA for business stakeholders. |
| **SRE / DevOps** | Recurring issue detection. | Retrieval of similar past incidents and their fixes. |

---

## 6. Core User Stories
1. **As an on-call engineer,** I want RootSight to ping Slack with an incident brief so I don't have to manually grep logs during a P0.
2. **As an investigator,** I want to see confidence scores on every hypothesis so I know which leads to prioritize.
3. **As an SRE,** I want to see if this incident looks like something we saw 3 months ago so I can apply the previous fix.
4. **As a lead engineer,** I want a ready-to-paste Jira ticket draft so I can focus on the fix, not the paperwork.

---

## 7. Core Product Flow
`Trigger (Webhook)` → `Sample Logs (100 lines)` → `Reconstruct Timeline (Gemini)` → `RCA Hypotheses (Gemini)` → `Impact Assessment (Gemini)` → `Memory Retrieval (FAISS)` → `Action Generation (Groq)` → `Final Brief`.

---

## 8. Functional Requirements

### Trigger & Ingestion (`trigger_service`, `ingestion_service`)
- The system SHALL accept webhooks from PagerDuty and Datadog.
- The system SHALL sample a maximum of 100 log lines per pipeline run.

### Intelligence (`timeline_module`, `rca_module`, `impact_module`)
- The system SHALL produce a chronological timeline with confidence scores.
- The system SHALL rank RCA hypotheses and provide supporting/counter evidence.
- The system SHALL mark any analysis with <30% confidence as "low-confidence".

### Memory & Actions (`memory_module`, `action_module`)
- The system SHALL retrieve the top 3 similar past incidents using local embeddings.
- The system SHALL generate Slack and Jira drafts in "pending" status.

---

## 9. Non-Functional Requirements
- **Performance:** Pipeline completion < 60s.
- **Reliability:** Graceful degradation if external logs are unreachable.
- **Cost:** $0.00 AI operating cost (Free-tier APIs).
- **Security:** No raw logs stored permanently; only summarized intelligence.

---

## 10. Free-First AI Stack

| Layer | Tool | Justification |
| :--- | :--- | :--- |
| **Reasoning** | Gemini 2.5 Flash | Best free-tier context window and reasoning. |
| **Formatting** | Groq (Llama 3) | Sub-second latency for message drafting. |
| **Embeddings** | Gemini Embeddings | High quality, consistent with reasoning LLM. |
| **Vector Store** | FAISS | Local, lightweight, no-cost. |

---

## 11. Architecture Overview
RootSight uses an async FastAPI backend serving a Next.js/Tailwind frontend. The pipeline is orchestrated as a sequence of discrete modules that communicate via a shared SQLite database.

---

## 12. Core Data Models
(See `execution_architecture.md` for full JSON schemas of Incident, Event, Hypothesis, Impact, SimilarIncident, and Action.)

---

## 13. Step-by-Step Execution Architecture
(See `execution_architecture.md` for detailed module responsibilities and failure modes.)

---

## 14. MVP Milestones

| Milestone | Deliverable | Priority |
| :--- | :--- | :--- |
| **M1: Core Pipeline** | Trigger to RCA output. | Critical |
| **M2: UI Dashboard** | Incident Brief visualization. | High |
| **M3: Memory** | Similarity search via FAISS. | Medium |
| **M4: Actions** | One-click Jira/Slack drafts. | Low |

---

## 15. Success Metrics

| Metric | Target | Why |
| :--- | :--- | :--- |
| **Time to Brief** | < 60s | Vital for active incident response. |
| **RCA Accuracy** | > 75% | Must be reliable enough to trust evidence. |
| **API Cost** | $0.00 | Core product constraint. |

---

## 16. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| LLM Rate Limits | Pipeline stalls. | Implement exponential backoff + log sampling. |
| Hallucination | False evidence. | Mandatory evidence links + confidence scoring. |
| Data Privacy | Log exposure. | Sampling only; no long-term raw log storage. |

---

## 17. Open Questions
- Should we support local file uploads for manual "bundle" analysis?
- What is the preferred frequency for memory indexing (real-time vs daily)?
