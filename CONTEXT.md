# Re:Learn — Active Project Context & State Machine
> Single source of truth for the project state. Updated continuously across development phases.

---

## 1. Project Identity & Goal
- **Project Name:** Re:Learn (Adaptive Multimodal Learning Environment)
- **Target Deadline:** Tomorrow, 11:00 AM demo presentation
- **Core Domain:** Introductory Programming in Python
- **Target Objective:** Diagnose underlying misconceptions (not just pass/fail), differentiate confusable misconceptions with 1-click micro-probes, provide multimodal memory-trace interventions, and expose fragile/suppressed learning.

---

## 2. Active Development Phase Tracker

| Phase | Description | Owner / Agent | Status | Verified Git Commit |
|---|---|---|---|---|
| **Phase 0** | Workspace, SQLite Schema, Repo Init | DB + Integration | ✅ Completed | `feat(core): initialize database models and workspace schema` |
| **Phase 1** | AST Extractor, Feature Engine, Sandbox | AI/ML + Backend | ✅ Completed | `feat(ml): implement AST parser and execution sandbox` |
| **Phase 2** | Tracer (`sys.settrace`), API Endpoints | Backend + Security | ✅ Completed | `feat(api): add execution tracer and diagnosis endpoints` |
| **Phase 3** | Dual-Pane Workspace, Monaco Editor, Radar Bars | Frontend | ✅ Completed | `feat(ui): complete unified workspace and micro-probe feed` |
| **Phase 4** | Multimodal Variable Memory-Box Component | Frontend + AI/ML | ✅ Completed | `feat(multimodal): add interactive memory-box trace visualizer` |
| **Phase 5** | Model Training, Calibration & Eval *(PAUSED on local request)* | AI/ML | **PAUSED (Waiting User Go-Ahead)** | — |
| **Phase 6** | Pre-seeded SQLite Presets & Model Inspector | DB + Frontend | ✅ Completed | `feat(eval): add fragile knowledge detection and model inspector` |
| **Phase 7** | Full Integration, Zero-Crash Smoke Test & Freeze | Integration + Security | 🔄 In Progress | — |

---

## 3. High-Priority Architectural Rules
1. **No External LLM Runtime Dependency:** Diagnosis and interventions run via deterministic ML classification, AST extraction, and pre-computed visual memory traces to eliminate latency and hallucination.
2. **Minimal-Click Probes:** Ambiguities (e.g., M1 vs. M2) are disambiguated by a single 3-button micro-probe rather than chat inputs.
3. **Multimodality via Dual-Coding:** Visual timeline scrubbers show memory addresses/values updating at every loop iteration.
4. **Fragile Knowledge Detection:** A learner passing a transfer problem but failing a counter-probe is marked `SUPPRESSED`.
5. **Local Compute Guardrail:** ML training and heavyweight tasks are held until the user explicitly permits or provides mock/pre-trained weights.

---

## 4. Completed File Index

### Backend
- `backend/app/__init__.py` — Package init
- `backend/app/config.py` — Runtime config (DB path, sandbox limits, CORS)
- `backend/app/db.py` — SQLAlchemy session factory + `init_db()` + `get_db()` dep
- `backend/app/models.py` — 7 SQLAlchemy models: `learners`, `problems`, `submissions`, `diagnoses`, `probe_events`, `reassessments`, `learner_misconceptions`
- `backend/app/main.py` — FastAPI app with CORS, auto-seed on startup, static serving
- `backend/app/api/submit.py` — `POST /api/submit`
- `backend/app/api/probe.py` — `POST /api/probe/answer`
- `backend/app/api/reassess.py` — `POST /api/reassess` (RESOLVED/SUPPRESSED/UNRESOLVED)
- `backend/app/api/inspector.py` — `GET /api/inspector`, `/api/inspector/problems`, `/api/inspector/learners`
- `backend/app/core/sandbox.py` — AST import blocker + 2s threading timeout runner
- `backend/app/core/tracer.py` — `sys.settrace` frame snapshot engine
- `backend/app/core/features.py` — AST structural parser (M0–M7) + execution signature generator
- `backend/app/core/classifier.py` — Heuristic Bayesian classifier (Phase 5 RF on hold)
- `backend/app/core/probe_bank.py` — 4 micro-probes + Bayesian update logic
- `backend/app/core/interventions.py` — Socratic intervention templates + memory-box builder

### Data
- `backend/data/taxonomy.json` — 8-class misconception taxonomy
- `backend/data/seed_data.py` — 5 problems + 5 preset judge learners

### ML (Phase 5 — PAUSED)
- `ml/generate_dataset.py` — Synthetic mutant dataset generator (blocked)
- `ml/train.py` — RandomForest + Isotonic Calibration (blocked)
- `ml/evaluate.py` — LOPO/LOMO evaluation (blocked)
- `ml/artifacts/` — Empty until Phase 5 approved

### Frontend (Zero-build-step React 18 via CDN)
- `frontend/index.html` — SPA shell (Monaco + React 18 + Babel CDN)
- `frontend/css/styles.css` — Full design system (dark glassmorphic, 500+ lines)
- `frontend/js/app.jsx` — Main app shell
- `frontend/js/components/EditorPane.jsx` — Header, ProblemBar, Toolbar, Console
- `frontend/js/components/MonacoEditor.jsx` — Monaco editor wrapper
- `frontend/js/components/RadarFeed.jsx` — M0–M7 confidence radar bars
- `frontend/js/components/MicroProbe.jsx` — 1-click probe selector + Bayesian feedback
- `frontend/js/components/Visualizer.jsx` — Memory-box interactive timeline
- `frontend/js/components/DiagnosisPanes.jsx` — DiagnosisPane, VisualizerPane, ReassessPane
- `frontend/js/components/Inspector.jsx` — Instructor modal (confusion matrix, LOPO, gain)

### Root
- `requirements.txt` — Python deps
- `run.sh` — One-command startup
- `CONTEXT.md` — Active project state machine
- `RULES.md` — Sub-agent roles, conduct & engineering guidelines
- `NEXT_STEPS.md` — Task matrix and future execution roadmap

---

## 5. Active Blockers
- None at this time. Phase 5 (ML training) is intentionally paused.
- Backend requires `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload` from project root.

---

## 6. Known Demo Paths (for judge validation)
| Path | Steps |
|---|---|
| M1 (Reinit) | Submit code with `s=0` inside loop → M1 diagnosis → Probe shows 9 → SUPPRESSED on counter |
| M2 (Print) | Submit code with `print(s)` no return → M2 diagnosis → probe shows None |
| M0 (Correct) | Submit passing code → M0 / 100% confidence → no probe needed |
| SUPPRESSED | Submit correct-looking code → Gate 1 pass → Gate 2 fail → SUPPRESSED badge |