# Re:Learn — Next Agent Execution Tasks & Roadmap

This document outlines the planned roadmap and remaining execution tasks for the agent team.

> **Operational Directive:** Every sub-agent executing tasks from this document MUST read and strictly obey the engineering standards and role-based conduct detailed in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).

---

## 📋 Task Matrix by Agent Role

### 1. ⚙️ Backend Engineer Tasks
- [ ] **Task B1: Real-time WebSocket Trace Streaming (Optional Enhancement)**
  * Implement WebSocket endpoint `/ws/trace` for real-time execution trace updates during longer executions.
  * Follow execution rules in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).
- [ ] **Task B2: Additional Misconception Taxonomy Expansion**
  * Extend `taxonomy.json` and `probe_bank.py` to support M8 (Off-by-One Loop Indexing) and M9 (Mutable Default Arguments).

### 2. 🧠 AI/ML Engineer Tasks
- [ ] **Task M1: Model Training Execution (Phase 5 Unfreeze)**
  * Upon explicit user approval, run `python ml/generate_dataset.py` to generate 5,000 synthetic Python mutants.
  * Run `python ml/train.py` to train RandomForest + Isotonic Calibration.
  * Save calibrated weights to `ml/artifacts/model.joblib`.
  * Follow AI/ML role directives in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).
- [ ] **Task M2: Evaluation & Metrics Export**
  * Execute `python ml/evaluate.py` for LOPO (Leave-One-Problem-Out) cross-validation.
  * Output `ml/artifacts/metrics.json` to populate the live Inspector confusion matrix.

### 3. 🏛️ Frontend Engineer Tasks
- [ ] **Task F1: Advanced Memory-Box Custom Visualizations**
  * Add visual pointer arrows for nested list/dictionary structures in `Visualizer.jsx`.
  * Adhere to UI visual excellence guidelines in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).
- [ ] **Task F2: Exportable Diagnostic PDF/Summary Reports**
  * Add a 1-click "Download Student Misconception Profile" export button in the Inspector View.

### 4. 🧪 Tester & Security Agent Tasks
- [ ] **Task T1: Extended Edge-Case Sandbox Fuzzing**
  * Fuzz `/api/submit` with infinite loop routines, stack overflow recursions, and large memory allocations to verify sandbox stability.
  * Enforce rules defined in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).
- [ ] **Task T2: Dual-Gate Counter-Probe Verification Suite**
  * Write automated test cases verifying that `SUPPRESSED` knowledge badges trigger correctly on failed counter-probes.

### 5. 🔗 Integration Engineer Tasks
- [ ] **Task I1: Single-Click Dockerization (Optional)**
  * Create `Dockerfile` and `docker-compose.yml` for unified backend/frontend production deployment.
- [ ] **Task I2: Final Demo Freeze & Presentation Polish**
  * Perform end-to-end dry run across all 4 demo paths listed in [`CONTEXT.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/CONTEXT.md).

---

## 📌 Execution Protocol

When starting a task from this file:
1. Open [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md) and locate your assigned role.
2. Verify all pre-conditions in [`CONTEXT.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/CONTEXT.md).
3. Execute changes, run verification, update `CONTEXT.md`, and commit progress to Git.
