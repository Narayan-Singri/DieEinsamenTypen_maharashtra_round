"""
Re:Learn FastAPI Application Server
Main entry point — wires up all routers and middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.app.config import settings
from backend.app.db import init_db
from backend.app.api import submit, probe, reassess, inspector

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Re:Learn API",
    description="Adaptive Multimodal Misconception Diagnosis System",
    version="1.0.0",
)

# CORS — allow all origins for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup event: initialize DB
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    init_db()
    # Auto-seed if database is empty
    from backend.app.db import SessionLocal
    from backend.app.models import Problem
    db = SessionLocal()
    try:
        count = db.query(Problem).count()
        if count == 0:
            from backend.data.seed_data import seed
            seed()
    finally:
        db.close()

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.include_router(submit.router, prefix="/api", tags=["Submission"])
app.include_router(probe.router, prefix="/api", tags=["Probe"])
app.include_router(reassess.router, prefix="/api", tags=["Reassessment"])
app.include_router(inspector.router, prefix="/api", tags=["Inspector"])

# ---------------------------------------------------------------------------
# Static file serving for frontend
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "1.0.0"}
