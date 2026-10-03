---

### File 3: `PROMPT.md`

```markdown
# Agent Execution Directives: Master Multi-Agent Orchestrator

You are an expert Principal AI Systems Engineer and Full-Stack Software Developer. Your objective is to build **Re:Learn** into a fully functional, demo-ready application before tomorrow 11:00 AM[cite: 2].

You must work strictly through the phased structure detailed below. Maintain and update `CONTEXT.md` after every phase. Ensure Git commits are tagged cleanly at every milestone.

---

## Sub-Agent Roster & Assigned Responsibilities

1. **Agent-Doc (Documentation & Standards):**
   - Keeps `CONTEXT.md` up to date with the latest commit hashes, current phase, and active blockers.
   - Ensures no dead code or placeholder comments exist in production paths.

2. **Agent-DB (Database & Schemas):**
   - Implements SQLAlchemy declarative models in `backend/app/models.py`.
   - Seeds problems, test cases, and judge demo presets in `backend/data/seed_data.py`.

3. **Agent-Security (Sandbox & Safety):**
   - Implements execution isolation in `backend/app/core/sandbox.py`[cite: 2].
   - Blocks unsafe AST imports (`os`, `sys`, `subprocess`, `socket`) and sets 2.0-second timeouts[cite: 2].

4. **Agent-AIML (Feature Extraction, Classifier & Evaluation):**
   - Builds AST structural parser and execution signature extractors[cite: 2].
   - Implements 1-click micro-probe logic and Bayesian updates[cite: 2].
   - **PAUSE DIRECTIVE:** Do NOT trigger local model training until instructed. Prepare the scripts (`ml/train.py`, `ml/generate_dataset.py`) and use pre-calibrated weights/heuristics for development.

5. **Agent-Backend (FastAPI & Trace Engine):**
   - Implements `tracer.py` using `sys.settrace` to record step-by-step memory frame states (`vars`, `line`, `event`)[cite: 2].
   - Exposes REST endpoints: `/api/submit`, `/api/probe/answer`, `/api/reassess`, `/api/inspector`[cite: 2].

6. **Agent-Frontend (Unified Workspace & Memory Visualizer):**
   - Builds zero-build-step React 18 interface with Monaco Editor and Tailwind CSS[cite: 2].
   - Implements Confidence Radar, 1-Click Micro-Probe buttons, and the interactive SVG/HTML memory-box timeline slider[cite: 2].
   - Adds the Judge Quick-Switcher dropdown at the top navigation bar.

7. **Agent-Integration (End-to-End Testing & Git Management):**
   - Verifies end-to-end data flow between backend APIs and UI components.
   - Manages Git branch hygiene and creates verified stage commits.

---

## Phased Execution Roadmap

### Phase 0: Workspace & Database Foundation
- **Tasks:**
  - Create full folder layout: `backend/`, `frontend/`, `ml/`.
  - Write `requirements.txt`:
    ```text
    fastapi>=0.109.0
    uvicorn>=0.27.0
    sqlalchemy>=2.0.0
    pydantic>=2.5.0
    scikit-learn>=1.3.0
    numpy>=1.24.0
    joblib>=1.3.0
    ```
  - Define database tables in `models.py`: `learners`, `problems`, `submissions`, `diagnoses`, `probe_events`, `reassessments`, `learner_misconceptions`[cite: 2].
  - Populate `seed_data.py` with 5 base problems and pre-configured preset cases.
- **Git Commit:** `git commit -m "feat(core): initialize database models and workspace schema"`

### Phase 1: Feature Extraction & Sandbox Runner
- **Tasks:**
  - Implement `backend/app/core/sandbox.py`: safe execution runner with 2-second timeout and blocked imports[cite: 2].
  - Implement `backend/app/core/features.py`:
    - AST feature extractor (e.g., assignment in loop bodies, `range(len - 1)`, return vs print)[cite: 2].
    - Execution signature generator (evaluates code on 5 fixed inputs: `[]`, `[1]`, `[1, 2]`, `[1, 2, 3]`, `[4, 9]`)[cite: 2].
- **Git Commit:** `git commit -m "feat(ml): implement AST parser and execution sandbox"`

### Phase 2: Variable State Tracer & Core API Routes
- **Tasks:**
  - Implement `backend/app/core/tracer.py`: attaches a tracing hook to record variable states at each loop iteration[cite: 2].
  - Implement FastAPI routes:
    - `POST /api/submit`: Runs code, computes execution signature + AST, returns diagnosis probabilities and probe requirement[cite: 2].
    - `POST /api/probe/answer`: Applies Bayesian probability update based on 1-click option selection[cite: 2].
    - `POST /api/reassess`: Evaluates transfer solution and counter-probe trap, returning `RESOLVED`, `SUPPRESSED`, or `UNRESOLVED`[cite: 2].
- **Git Commit:** `git commit -m "feat(api): add execution tracer and diagnosis endpoints"`

### Phase 3: Dual-Pane Unified UI Shell
- **Tasks:**
  - Build `frontend/index.html` loading React 18, Babel, Monaco Editor, and Tailwind CSS via CDN[cite: 2].
  - Implement left pane: Monaco editor, problem description, Run/Submit buttons[cite: 2].
  - Implement right pane:
    - Confidence Radar bars (`M1`, `M2`, `M0`, etc.)[cite: 2].
    - Minimal-Click Micro-Probe card with 3 options (`(A) 9`, `(B) 4`, `(C) 13`)[cite: 2].
    - Judge Quick-Switcher dropdown at top header.
- **Git Commit:** `git commit -m "feat(ui): complete unified workspace and micro-probe feed"`

### Phase 4: Multimodal Memory-Box Timeline Visualizer
- **Tasks:**
  - Implement `frontend/js/components/Visualizer.jsx`:
    - Reads frame snapshots from `/api/submit` trace output.
    - Draws variable boxes (`nums`, `n`, `s`) step by step.
    - Highlights iteration 2 accumulator overwrite in red: `s: 4 -> 0`.
    - Includes interactive playback controls: [Prev], [Next], [Play/Pause], and scrub slider.
- **Git Commit:** `git commit -m "feat(multimodal): add interactive memory-box trace visualizer"`

### Phase 5: Local ML Model Training (PAUSED - WAITING APPROVAL)
- **Status:** **HOLD.** Do NOT run model training automatically.
- **Tasks When Resumed:**
  - Execute `ml/generate_dataset.py` to create synthetic training data[cite: 2].
  - Run `ml/train.py` using `RandomForestClassifier` with isotonic calibration[cite: 2].
  - Export metrics to `ml/artifacts/metrics.json`[cite: 2].

### Phase 6: Dual-Gate Fragile Knowledge Engine & Inspector Modal
- **Tasks:**
  - Implement `reassess.py` logic to detect superficial fixes[cite: 2].
  - Add the **"⚠️ SUPPRESSED: Fragile Knowledge Detected"** badge to the frontend[cite: 2].
  - Build the Instructor / Model Inspector modal showing confusion matrix and Leave-One-Problem-Out metrics[cite: 2].
- **Git Commit:** `git commit -m "feat(eval): add fragile knowledge detection and model inspector"`

### Phase 7: End-to-End Verification & Code Freeze
- **Tasks:**
  - Validate preset paths (M1 vs M2 collision, disambiguation probe, memory visualization, counter-probe trap)[cite: 2].
  - Verify system operates offline without network latency[cite: 2].
  - Perform code freeze.
- **Git Commit:** `git commit -m "release: v1.0.0 freeze for hackathon presentation"`