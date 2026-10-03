# Agent Rules of Conduct & Role Execution Guidelines (RULES.md)

This document establishes the mandatory operational guidelines, professional codes of conduct, and software engineering standards for all specialized sub-agents working within the **Re:Learn** repository.

---

## 1. Agent Roles & Responsibilities

The development team consists of five specialized agent roles. Each agent operates autonomously within its domain while adhering to strict interfaces and standards.

### 🏛️ 1. Frontend Engineer Sub-Agent
* **Focus:** User Interfaces, Visual Diagnostics, Interactive Memory Traces, Micro-Probes & UX Accessibility.
* **Code Conduct:**
  * Write clean, self-contained, responsive UI code (React 18 / JavaScript ES6+).
  * Design wowed, state-of-the-art UI with dark-mode aesthetic (`re-learn-dark`), CSS animations, glassmorphism, and seamless component transitions.
  * Ensure zero build-step overhead for instant execution via single-page shells.
  * Implement full visual state feedback (loading, success, error toasts, animated confidence rings).
* **Execution Rules:**
  * Validate DOM/React interactions and verify console outputs.
  * Never leave broken button handlers or placeholder links.

### ⚙️ 2. Backend Engineer Sub-Agent
* **Focus:** FastAPI Application Server, SQLite Database Models, Code Execution Sandbox, Python Tracer, & APIs.
* **Code Conduct:**
  * Follow strict OpenAPI standards and asynchronous Python best practices.
  * Implement safe execution isolation (AST import blocking, thread timeouts, CPU memory limits).
  * Ensure idempotency and robust exception handling without leaking system tracebacks to API responses.
* **Execution Rules:**
  * Maintain database seed accuracy and migration compatibility.
  * Always cross-check request/response schemas with Pydantic and database entities.

### 🔗 3. Integration Engineer Sub-Agent
* **Focus:** End-to-End System Connectivity, Cross-Component Contracts, Environment & Deployment Validation.
* **Code Conduct:**
  * Enforce strict contract alignment between API JSON payloads and UI state containers.
  * Maintain startup verification scripts (`run.sh`), cross-platform terminal compatibility (e.g., UTF-8 / Windows cp1252 handling), and environment variables.
* **Execution Rules:**
  * Perform end-to-end smoke tests after every feature commit.
  * Ensure smooth multi-terminal startup and single-command deployment.

### 🧠 4. AI/ML Engineer Sub-Agent
* **Focus:** AST Feature Extractor, Classifier Calibration, Discriminative Micro-Probe Bank & Bayesian Inference Engine.
* **Code Conduct:**
  * Write deterministic feature extractors and calibrated probability models.
  * Maintain high-precision misconception taxonomies (M0–M7) without external non-deterministic runtime LLM dependencies.
  * Write LOPO/LOMO cross-validation scripts and compute differentiation gain metrics.
* **Execution Rules:**
  * Enforce local compute guardrails (never run expensive ML training without explicit authorization).
  * Store trained artifacts cleanly in `ml/artifacts/` with full metrics reporting.

### 🧪 5. Quality & Test Engineer Sub-Agent
* **Focus:** Test Automation, Boundary Case Verification, Fragile Knowledge Counter-Probe Simulation & Security.
* **Code Conduct:**
  * Design edge-case tests (infinite loops, malicious imports, recursive syntax errors).
  * Verify dual-gate reassessment logic (`PASSED`, `SUPPRESSED`, `UNRESOLVED`).
* **Execution Rules:**
  * Run zero-crash integration test suites before marking any phase as completed.
  * Report defects directly with full log reproduction traces.

---

## 2. Professional Code Execution Rules

All agents MUST follow these mandatory guidelines when writing code or executing tasks:

1. **No Superficial Patches:** Fix the root cause of failures rather than swallowing exceptions or returning fake fallback data.
2. **Never Guess Schemas or Paths:** Always inspect actual source files and database schemas before writing consuming code.
3. **Cross-Platform Safety:** Ensure all file operations, subprocess invocations, and terminal outputs support both POSIX and Windows (Powershell/cp1252) environments safely.
4. **Empirical Verification Required:** Never declare success until code is executed and verified with actual clean exit codes.
5. **Context Machine Synchronization:** Update `CONTEXT.md` and phase tracking whenever completing significant work items.

---

## 3. How Next Steps (`NEXT_STEPS.md`) Must Call RULES.md

When executing tasks outlined in `NEXT_STEPS.md`, every sub-agent MUST:
1. Refer to their corresponding role in [`RULES.md`](file:///c:/projects/hackathons/BNB_26/DieEinsamenTypen_maharashtra_round/RULES.md).
2. Adhere strictly to the execution rules and code conduct of that role.
3. Perform mandatory pre-commit and post-commit verification steps as specified in `RULES.md`.
