# RootSight — Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2026-04-16  
**Author:** RootSight Core Team  
**Status:** Draft — MVP Scope

---

## 1. Product Overview

RootSight is an AI-powered incident understanding and action system. It sits on top of existing monitoring and alerting tools (PagerDuty, Datadog, CloudWatch) and automates the cognitive work that engineers currently do manually during incidents: reconstructing what happened, figuring out why, assessing impact, and deciding what to do next.

RootSight does **not** replace your alerting stack. It replaces the 30–90 minutes of investigative scrambling that follows the alert.

**Core output:** A structured incident brief containing a timeline, confidence-scored root-cause hypotheses, quantified impact, similar incident matches, and executable follow-up actions — delivered in minutes.

---

## 2. Problem Statement

### The Gap

Modern engineering teams have solved **detection** (Datadog, Prometheus, CloudWatch) and **notification** (PagerDuty, OpsGenie). What's still manual is **understanding**:

| Phase | Tool Coverage | Manual Effort |
|---|---|---|
| Detection | ✅ Monitoring tools | Low |
| Notification | ✅ PagerDuty / OpsGenie | Low |
| **Understanding** | ❌ No tool | **High — 30-90 min** |
| Resolution | Partial (runbooks) | Medium-High |

### What engineers actually do after an alert fires

1. Open 3–5 tabs across monitoring tools
2. Manually scan logs for anomalies
3. Mentally reconstruct a timeline
4. Guess at root causes based on pattern recognition
5. Estimate blast radius with incomplete data
6. Write a Slack update or incident summary
7. Create a Jira ticket
8. (Later) Write a post-mortem from memory

**Every step above is a cognitive task that can be structured, automated, and made evidence-based.**

### Cost of the Status Quo

- **MTTR inflation:** Manual investigation adds 30–90 minutes to every incident
- **Knowledge loss:** Incident context lives in engineers' heads, not systems
- **Inconsistency:** Quality of root-cause analysis depends on who's on-call
- **Fatigue and burnout:** Repetitive investigative work during high-stress incidents
- **Slow post-mortems:** Written days later from degraded memory

---

## 3. Goals

### Primary Goals (MVP)

| # | Goal | Measurable Outcome |
|---|---|---|
| G1 | Automate incident timeline reconstruction | Timeline generated in < 2 min from log ingestion |
| G2 | Generate evidence-backed RCA hypotheses | Top 2–3 hypotheses with confidence scores + evidence links |
| G3 | Quantify incident impact | Affected services, severity, estimated duration, user impact |
| G4 | Surface similar past incidents | Top match with similarity reason and prior fix |
| G5 | Prepare follow-up actions | Draft Jira ticket + Slack update generated automatically |
| G6 | Demonstrate credible, trustworthy reasoning | No false certainty, clear confidence bands, explicit unknowns |

### Stretch Goals (Post-MVP)

- Auto-execute safe actions (Jira creation, Slack post) with approval gate
- Confluence post-mortem generation
- Multi-incident correlation (detect cascading failures)
- Custom runbook triggering
- Learning loop: RCA accuracy tracking over time

---

## 4. Non-Goals

> [!IMPORTANT]
> These are explicitly out of scope. RootSight must not drift into these areas for MVP.

| Non-Goal | Reason |
|---|---|
| Replace PagerDuty or Datadog | RootSight is a layer on top, not a competitor |
| Full autonomous remediation | Unsafe without extensive guardrails; MVP focuses on understanding |
| Build a monitoring/observability platform | Commodity market; not our differentiator |
| Guarantee root-cause correctness | Fundamentally impossible; we provide ranked hypotheses with evidence |
| Support all log formats day one | Start with Datadog JSON + PagerDuty webhooks |
| Real-time streaming analysis | MVP is event-triggered batch analysis, not continuous streaming |

---

## 5. Target Users

### Primary Persona: On-Call Engineer (SRE / Platform)

- **Role:** Site Reliability Engineer, Platform Engineer, DevOps Engineer
- **Context:** Receives a PagerDuty alert at 2 AM, needs to understand what's happening fast
- **Pain:** Spends 30–60 minutes jumping between tools to reconstruct the incident
- **Need:** A pre-built incident brief with timeline, probable causes, and next steps
- **Trust bar:** Won't trust a tool that gives one black-box answer. Needs to see evidence and confidence levels.

### Secondary Persona: Engineering Manager / Incident Commander

- **Role:** Leads incident response, coordinates communication
- **Context:** Needs a clear summary to share with stakeholders quickly
- **Pain:** Depends on on-call engineer's verbal update; no structured artifact
- **Need:** Shareable incident brief with impact assessment and action items

### Tertiary Persona: Post-Mortem Author

- **Role:** Writes post-incident reviews
- **Context:** Reconstructing the incident days later from memory and scattered logs
- **Pain:** Incomplete recall, missing evidence, inconsistent format
- **Need:** Pre-structured timeline and RCA draft to build the post-mortem from

---

## 6. User Stories

### US-1: Incident Understanding

> As an on-call engineer, when I receive a PagerDuty alert, I want RootSight to automatically analyze relevant logs and produce a structured incident brief so I can understand the incident in under 3 minutes instead of 30.

**Acceptance Criteria:**
- Brief includes timeline, RCA hypotheses, impact, and actions
- Generated within 3 minutes of trigger
- Confidence scores on all hypotheses
- Evidence links back to source logs

### US-2: Historical Pattern Matching

> As an SRE, I want RootSight to tell me if this incident resembles something we've seen before, so I can apply known fixes faster.

**Acceptance Criteria:**
- Retrieves top similar incident from memory store
- Shows similarity reason and prior resolution
- Falls back gracefully when no match exists ("No strong historical match found")

### US-3: Action Preparation

> As an incident commander, I want RootSight to draft a Jira ticket and Slack update so I can communicate status without writing from scratch.

**Acceptance Criteria:**
- Jira ticket draft includes title, description, severity, labels
- Slack message includes summary, impact, current status
- All actions require human approval before execution in MVP

### US-4: Trust and Transparency

> As an engineer, I want to see *why* RootSight reached each conclusion, so I can trust or override its analysis.

**Acceptance Criteria:**
- Each hypothesis shows supporting evidence, contradicting evidence, and missing information
- Confidence scores are calibrated (not always "95%")
- System explicitly states when data is insufficient

---

## 7. MVP Scope

### In Scope

```
✅ PagerDuty webhook ingestion (or simulated webhook)
✅ Datadog log collection via API
✅ Log normalization and noise filtering
✅ Chronological timeline reconstruction
✅ Top 2–3 RCA hypotheses with confidence, evidence, contradictions
✅ Basic impact analysis (services, severity, duration, user impact estimate)
✅ Similar incident retrieval from vector store
✅ Jira ticket draft generation
✅ Slack message draft generation
✅ Streamlit demo UI
✅ Simulated incident demo with pre-seeded data
```

### Out of Scope (MVP)

```
❌ Auto-execution of actions without approval
❌ CloudWatch integration (Datadog only for MVP)
❌ Real-time streaming ingestion
❌ Multi-incident correlation
❌ Custom runbook execution
❌ Confluence integration
❌ User authentication / multi-tenancy
❌ Production deployment hardening
```

---

## 8. Functional Requirements

### FR-1: Alert Ingestion

| Requirement | Detail |
|---|---|
| FR-1.1 | Accept PagerDuty V2 webhook payload via HTTP POST |
| FR-1.2 | Parse incident ID, service, severity, timestamp, description |
| FR-1.3 | Support simulated webhook for demo mode |
| FR-1.4 | Validate payload schema; reject malformed inputs with error |

### FR-2: Log Collection

| Requirement | Detail |
|---|---|
| FR-2.1 | Query Datadog Logs API for service + time window |
| FR-2.2 | Accept configurable time window (default: alert time ± 30 min) |
| FR-2.3 | Normalize log entries to common schema: `{timestamp, level, service, message, metadata}` |
| FR-2.4 | Filter noise (health checks, heartbeats, debug-level spam) |
| FR-2.5 | Support mock log injection for demo scenarios |

### FR-3: Timeline Reconstruction

| Requirement | Detail |
|---|---|
| FR-3.1 | Extract meaningful events from normalized logs |
| FR-3.2 | Classify events by type (deploy, error spike, latency, DB failure, etc.) |
| FR-3.3 | Sort chronologically |
| FR-3.4 | Deduplicate near-identical events within 5-second windows |
| FR-3.5 | Output structured timeline array |

### FR-4: Root Cause Analysis

| Requirement | Detail |
|---|---|
| FR-4.1 | Generate 2–3 ranked hypotheses |
| FR-4.2 | Each hypothesis includes: statement, confidence (0–100), supporting evidence, contradicting evidence, missing info |
| FR-4.3 | Confidence scores reflect actual evidence strength, not inflated defaults |
| FR-4.4 | Use Gemini as primary reasoning model for hypothesis generation |
| FR-4.5 | Prompt engineering enforces evidence-based language ("likely", "suggests", "consistent with") |

### FR-5: Impact Analysis

| Requirement | Detail |
|---|---|
| FR-5.1 | Identify affected service(s) and dependencies |
| FR-5.2 | Estimate incident duration from first error to recovery |
| FR-5.3 | Assign severity level (P1–P4) |
| FR-5.4 | Provide qualitative user/business impact estimate |
| FR-5.5 | Note when impact data is insufficient for quantification |

### FR-6: Memory / Similar Incident Retrieval

| Requirement | Detail |
|---|---|
| FR-6.1 | Embed incident summaries into vector store (FAISS or Chroma) |
| FR-6.2 | On new incident, retrieve top-1 similar incident |
| FR-6.3 | Return: title, similarity score, prior root cause, prior resolution |
| FR-6.4 | Graceful fallback: "No strong historical match found" |
| FR-6.5 | Allow manual addition of past incidents to seed the store |

### FR-7: Action Generation

| Requirement | Detail |
|---|---|
| FR-7.1 | Generate Jira ticket payload (title, description, severity, labels, assignee suggestion) |
| FR-7.2 | Generate Slack message (summary, impact, actions, status) |
| FR-7.3 | All actions are draft-only in MVP (no auto-execution) |
| FR-7.4 | Mark irreversible actions with "requires approval" tag |

### FR-8: Demo UI

| Requirement | Detail |
|---|---|
| FR-8.1 | Streamlit-based single-page application |
| FR-8.2 | Trigger button or webhook simulator to start incident analysis |
| FR-8.3 | Display: incident header, timeline, hypotheses, impact, similar incidents, actions |
| FR-8.4 | Visual confidence score indicators |
| FR-8.5 | Expandable evidence sections for each hypothesis |

---

## 9. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| **Performance** | End-to-end analysis time | < 3 minutes for typical incident |
| **Performance** | Log ingestion + normalization | < 30 seconds for 10K log lines |
| **Reliability** | Graceful degradation | If one agent fails, others continue with reduced confidence |
| **Reliability** | Retry logic on API failures | 3 retries with exponential backoff |
| **Security** | API keys | Stored in environment variables, never hardcoded |
| **Security** | No PII in logs | Filter or mask sensitive data in log processing |
| **Scalability** | MVP log volume | Up to 50K log entries per incident |
| **Maintainability** | Agent modularity | Each agent is independently testable and replaceable |
| **Observability** | Internal logging | Structured logs for each agent's execution |
| **Usability** | Demo readiness | Full incident walkthrough completable in < 5 min live demo |

---

## 10. Success Metrics

### Demo Success (Hackathon / Pitch)

| Metric | Target |
|---|---|
| Time to incident brief from alert trigger | < 3 minutes |
| Hypothesis accuracy on seeded scenarios | ≥ 1 correct hypothesis in top-3 |
| Audience comprehension of output | Timeline + hypotheses readable in < 30 sec |
| Demo completion without failures | 100% of demo runs complete end-to-end |

### Product Success (Post-MVP)

| Metric | Target |
|---|---|
| MTTR reduction | 30–50% reduction for investigated incidents |
| Engineer satisfaction score | ≥ 4/5 on usefulness survey |
| Hypothesis relevance score | ≥ 70% of hypotheses rated "relevant" by reviewers |
| Action adoption rate | ≥ 50% of suggested Jira/Slack drafts used as-is or lightly edited |
| Incident memory hit rate | ≥ 30% of incidents match a useful historical pattern |

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **LLM hallucination in RCA** | High | High | Confidence scores, evidence linking, explicit "missing info" fields, prompt guardrails |
| **Datadog API rate limits** | Medium | Medium | Cache logs, batch requests, configurable time windows |
| **Poor log quality from source** | High | Medium | Data quality check step; degrade confidence explicitly |
| **Demo failure during live pitch** | Medium | High | Pre-seeded demo mode with deterministic inputs; fallback to recorded demo |
| **Overengineering for MVP** | Medium | Medium | Strict scope gates; no features beyond checklist |
| **CrewAI orchestration complexity** | Medium | Medium | Start with simple sequential execution; add parallelism later |
| **Vector search returning irrelevant matches** | Medium | Low | Similarity threshold; explicit "no match" fallback |
| **Gemini latency on complex prompts** | Low-Medium | Medium | Prompt optimization; optional Groq fallback for summarization |

---

## 12. Open Questions

> [!WARNING]
> These must be resolved before or during implementation.

| # | Question | Impact | Owner |
|---|---|---|---|
| OQ-1 | Do we use real Datadog/PagerDuty API keys for the demo, or fully simulated data? | Demo fidelity vs. setup complexity | Product |
| OQ-2 | Should the Memory Agent use FAISS (simpler, local) or Chroma (more features, server)? | Architecture complexity | Engineering |
| OQ-3 | How many pre-seeded incidents do we need for a credible memory demo? | Demo quality | Product + Engineering |
| OQ-4 | Should the Streamlit UI include a "manual trigger" mode for ad-hoc log paste-in? | Scope creep risk | Product |
| OQ-5 | What Gemini model variant (Pro, Flash) gives the best cost/quality tradeoff for RCA? | Cost + quality | Engineering |
| OQ-6 | Do we need a database for incident storage, or is file-based JSON sufficient for MVP? | Engineering effort | Engineering |
| OQ-7 | Should the Action Agent actually call Jira/Slack APIs, or only generate payloads? | Demo impressiveness vs. scope | Product |

---

## 13. Milestones

### Phase 1: Foundation (Days 1–2)

- [ ] Project scaffolding and folder structure
- [ ] Core schemas defined (incident, timeline, hypothesis, impact, action)
- [ ] PagerDuty webhook parser (+ simulated mode)
- [ ] Datadog log fetcher (+ mock data mode)
- [ ] Log normalization pipeline
- [ ] Basic Gemini integration working

### Phase 2: Intelligence Core (Days 3–4)

- [ ] Timeline Agent — event extraction and reconstruction
- [ ] RCA Agent — hypothesis generation with confidence scores
- [ ] Impact Agent — severity and blast radius estimation
- [ ] Memory Agent — FAISS/Chroma index with seed data
- [ ] Schema validation across all agents

### Phase 3: Actions + Orchestration (Day 5)

- [ ] Action Agent — Jira + Slack payload generation
- [ ] Manager Agent — full pipeline orchestration via CrewAI
- [ ] Error handling and graceful degradation
- [ ] End-to-end test with simulated incident

### Phase 4: Demo UI + Polish (Days 6–7)

- [ ] Streamlit UI — incident trigger, timeline view, hypothesis cards, impact panel, actions
- [ ] Visual polish — confidence bars, expandable evidence, severity badges
- [ ] Demo script and pre-seeded scenario
- [ ] Dry-run demo rehearsal
- [ ] README and setup documentation

---

> [!NOTE]
> This PRD is scoped for a credible MVP and demo. Post-MVP features (autonomous execution, multi-incident correlation, learning loops) are intentionally excluded to maintain focus and avoid overpromising.
