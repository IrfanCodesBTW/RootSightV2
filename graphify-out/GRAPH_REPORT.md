# Graph Report - F:\projects\RootSIghtV2  (2026-04-22)

## Corpus Check
- 39 files · ~9,386 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 151 nodes · 295 edges · 25 communities detected
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]

## God Nodes (most connected - your core abstractions)
1. `Incident` - 14 edges
2. `analyze_root_cause()` - 10 edges
3. `build_timeline()` - 10 edges
4. `generate_actions()` - 9 edges
5. `Calls Groq (Llama 3) to rapidly format incident data into actionable drafts` - 9 edges
6. `run_pipeline_async()` - 9 edges
7. `HypothesisList` - 9 edges
8. `find_similar_incidents()` - 8 edges
9. `start_pipeline()` - 8 edges
10. `EventList` - 8 edges

## Surprising Connections (you probably didn't know these)
- `generate_actions()` --calls--> `test_generate_actions()`  [INFERRED]
  rootsight\backend\action_module.py → rootsight\tests\test_memory_actions.py
- `Impact` --calls--> `sample_impact()`  [INFERRED]
  rootsight\backend\schemas\impact.py → rootsight\tests\test_memory_actions.py
- `Incident` --calls--> `sample_incident()`  [INFERRED]
  rootsight\backend\schemas\incident.py → rootsight\tests\test_memory_actions.py
- `Product Vision` --represents--> `RootSight Logo`  [INFERRED]
  PRD.md → rootsight/frontend/public/logo.png
- `generate_actions()` --calls--> `format_json()`  [INFERRED]
  rootsight\backend\action_module.py → rootsight\backend\llm_clients\groq_client.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (8): BaseSettings, Settings, create_db_and_tables(), list_incidents(), on_startup(), Returns all incidents processed by the system., get_all_incidents(), SQLModel

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (18): Incident, IncidentBase, IncidentCreate, ingest_logs(), Fetches, filters, and samples logs for the given incident.     Returns a maximum, RawEvent, get_incident_status(), Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.28
Nodes (14): Action, ActionList, ActionType, ApprovalStatus, ExecutionStatus, generate_actions(), Calls Groq (Llama 3) to rapidly format incident data into actionable drafts, Enum (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.32
Nodes (9): Hypothesis, HypothesisList, analyze_root_cause(), _fallback_hypothesis(), Calls Gemini to generate root cause hypotheses based ONLY on the compressed time, sample_hypotheses(), sample_incident(), test_analyze_root_cause_empty() (+1 more)

### Community 4 - "Community 4"
Cohesion: 0.25
Nodes (9): BaseModel, find_similar_incidents(), Finds similar historical incidents using FAISS and asks Gemini to explain the si, SimilarIncident, SimilarIncidentList, sample_impact(), sample_incident(), test_find_similar_incidents() (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (9): Event, EventList, EventType, sample_event_list(), sample_incident(), test_build_timeline_empty(), test_build_timeline_success(), build_timeline() (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.43
Nodes (1): VectorStore

### Community 7 - "Community 7"
Cohesion: 0.57
Nodes (5): Impact, analyze_impact(), _fallback_impact(), Calls Gemini to estimate the business and user impact of the incident., SeverityBand

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (5): generate(), format_json(), test_gemini_client_retry_json_error(), test_gemini_client_success(), test_groq_client_success()

### Community 9 - "Community 9"
Cohesion: 0.29
Nodes (7): RootSight Logo, Action Generation, Memory Retrieval, Pipeline Flow, RCA Hypothesis Generation, RootSight PRD, Product Vision

### Community 10 - "Community 10"
Cohesion: 0.4
Nodes (3): getIncidentStatus(), triggerPipeline(), handleStartDemo()

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Returns the current state of the pipeline for a specific incident.

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Returns all incidents processed by the system.

## Knowledge Gaps
- **13 isolated node(s):** `Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl`, `Returns the current state of the pipeline for a specific incident.`, `Returns all incidents processed by the system.`, `Entry point. Validates payload, creates incident, starts background task.`, `Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (2 nodes): `RootLayout()`, `layout.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (2 nodes): `BottomBar()`, `BottomBar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `CenterPanel()`, `CenterPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `RightPanel()`, `RightPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `utils.ts`, `cn()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `eslint.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `postcss.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Returns the current state of the pipeline for a specific incident.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Returns all incidents processed by the system.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Incident` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `run_pipeline_async()` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `find_similar_incidents()` connect `Community 4` to `Community 0`, `Community 8`, `Community 2`, `Community 6`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `str` (e.g. with `generate_actions()` and `ingest_logs()`) actually correct?**
  _`str` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Incident` (e.g. with `handle_trigger()` and `sample_incident()`) actually correct?**
  _`Incident` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `analyze_root_cause()` (e.g. with `run_pipeline_async()` and `generate()`) actually correct?**
  _`analyze_root_cause()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Triggers the RootSight intelligence pipeline.     Accepts PagerDuty/Datadog payl`, `Returns the current state of the pipeline for a specific incident.`, `Returns all incidents processed by the system.` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._