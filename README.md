# Re:Learn — Adaptive Multimodal Learning Environment

Re:Learn is an AI-driven programming education environment designed to diagnose, differentiate, and visually resolve deep-seated cognitive misconceptions in introductory Python[cite: 1, 2].

---

## 1. Directory Structure

```text
relearn/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application server
│   │   ├── config.py            # Global runtime configuration
│   │   ├── db.py                # SQLite connection & session management
│   │   ├── models.py            # SQLAlchemy database tables
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── submit.py        # /api/submit (Runs code, extracts AST, triggers diagnosis)
│   │   │   ├── probe.py         # /api/probe/answer (Bayesian update on micro-probes)
│   │   │   ├── reassess.py      # /api/reassess (Dual-gate transfer & counter-probe)
│   │   │   └── inspector.py     # /api/inspector (Metrics, LOPO & confusion matrix)
│   │   └── core/
│   │       ├── sandbox.py       # Isolated execution runner with limits
│   │       ├── tracer.py        # sys.settrace variable state snapshot engine
│   │       ├── features.py      # AST structural parsing + execution signature
│   │       ├── classifier.py    # Probabilistic inference & confidence calibration
│   │       ├── probe_bank.py    # Minimal-click discriminating micro-probes
│   │       └── interventions.py # Socratic code annotations & visual state builders
│   └── data/
│       ├── taxonomy.json        # 8-class misconception taxonomy definition
│       ├── seed_data.py         # Pre-seeded test problems, presets, and inspector data
│       └── relearn.db           # SQLite database instance
├── ml/
│   ├── generate_dataset.py      # Synthetic code mutator generator (M1–M8)
│   ├── train.py                 # Scikit-learn Random Forest + Isotonic Calibration
│   ├── evaluate.py              # LOPO, LOMO, and differentiation gain evaluation
│   └── artifacts/
│       ├── model.joblib         # Calibrated classifier weights
│       └── metrics.json         # Evaluation benchmarks and confusion matrix
├── frontend/
│   ├── index.html               # Unified single-page shell (React 18 CDN + Tailwind)
│   ├── css/
│   │   └── styles.css           # Workspace styling & memory-box animations
│   └── js/
│       ├── app.jsx              # Dual-pane IDE, Monaco integration, state feeds
│       ├── components/
│       │   ├── EditorPane.jsx   # Monaco code editor & console output
│       │   ├── RadarFeed.jsx    # Probabilistic confidence radar bars
│       │   ├── MicroProbe.jsx   # 1-click discriminative probe selector
│       │   ├── Visualizer.jsx   # Interactive memory-box lifecycle timeline
│       │   └── Inspector.jsx    # Instructor view, confusion matrix & LOPO stats
├── CONTEXT.md                   # Real-time state machine for agents
├── NEXT_STEPS.md                # Task roadmap referencing RULES.md
├── RULES.md                     # Agent roles, professional codes & conduct
├── PROMPT.md                    # Master agent execution directives
├── requirements.txt             # Python dependencies
└── run.sh                       # One-command startup script