"""
FastAPI Backend Server for Flame in Freefall.
Connects the existing RAG pipeline, knowledge graph, and NASA datasets
to the high-performance modern web frontend.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import APP_TITLE, TOP_K_RESULTS
from core.gemini_client import GeminiClient
from core.ingestion import load_and_chunk_data
from core.knowledge_graph import KnowledgeGraph
from core.memory import ConversationMemory
from core.rag_pipeline import RAGPipeline
from core.vectorstore import VectorStore
from utils.data_loader import (
    get_experiment_by_id,
    get_material_by_name,
    load_all_data,
    load_experiments,
    load_findings,
    load_materials,
    load_safety_guidelines,
)
from utils.helpers import clean_markdown_text, color_for_risk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlameServer")

app = FastAPI(title=APP_TITLE, version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton Core Engine State ────────────────────────────────────────────────
class EngineState:
    def __init__(self):
        self.all_data = load_all_data()
        self.kg = KnowledgeGraph()
        self.kg.build_from_data(self.all_data.get("experiments", []))
        self.vectorstore = VectorStore()
        if self.vectorstore.get_collection_stats().get("document_count", 0) == 0:
            chunks = load_and_chunk_data()
            if chunks:
                self.vectorstore.add_documents(chunks)
        self.gemini = GeminiClient()
        self.memory = ConversationMemory()
        self.rag = RAGPipeline(
            vectorstore=self.vectorstore,
            knowledge_graph=self.kg,
            gemini_client=self.gemini,
            memory=self.memory,
        )


engine = EngineState()


# ── Request / Response Models ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


class ScoreRequest(BaseModel):
    material: str
    environment: str
    oxygen_level: str


# ── API Endpoints ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "title": APP_TITLE,
        "ai_engine": "Gemini 2.5 Live" if engine.gemini.is_configured else "Local Knowledge Grounding",
        "experiments_count": len(engine.all_data.get("experiments", [])),
    }


@app.get("/api/stats")
def get_stats():
    exp_list = engine.all_data.get("experiments", [])
    mat_list = engine.all_data.get("materials", [])
    find_list = engine.all_data.get("findings", [])
    guide_list = engine.all_data.get("guidelines", [])

    # Group categories
    categories = {}
    for e in exp_list:
        cat = e.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    # Group material types
    mat_types = {}
    for m in mat_list:
        cat = m.get("category", "Other")
        mat_types[cat] = mat_types.get(cat, 0) + 1

    return {
        "total_experiments": len(exp_list),
        "materials_tested": len(mat_list),
        "key_findings": len(find_list),
        "safety_guidelines": len(guide_list),
        "categories": categories,
        "material_types": mat_types,
        "ai_configured": engine.gemini.is_configured,
    }


@app.get("/api/experiments")
def list_experiments(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
):
    exps = engine.all_data.get("experiments", [])
    if query:
        q = query.lower()
        exps = [
            e for e in exps
            if q in e.get("name", "").lower()
            or q in e.get("description", "").lower()
            or any(q in str(m).lower() for m in e.get("materials_tested", []))
            or any(q in str(f).lower() for f in e.get("key_findings", []))
        ]
    if category and category != "All Categories":
        exps = [e for e in exps if e.get("category") == category]
    if platform and platform != "All Platforms":
        exps = [e for e in exps if e.get("platform") == platform]

    return {"experiments": exps}


@app.get("/api/materials")
def list_materials():
    return {"materials": engine.all_data.get("materials", [])}


@app.get("/api/findings")
def list_findings():
    return {"findings": engine.all_data.get("findings", [])}


@app.get("/api/guidelines")
def list_guidelines():
    return {"guidelines": engine.all_data.get("guidelines", [])}


@app.get("/api/compare")
def compare_experiments(e1: str = Query("SAFFIRE-IV"), e2: str = Query("BASS-II")):
    exp_metrics = {
        "SAFFIRE": {"flame_spread": 7.2, "extinction_time": 6.8, "soot_yield": 5.5, "heat_release": 6.5, "safety_score": 7.2},
        "BASS": {"flame_spread": 5.8, "extinction_time": 7.5, "soot_yield": 4.5, "heat_release": 7.8, "safety_score": 6.5},
        "SoFIE": {"flame_spread": 3.2, "extinction_time": 8.5, "soot_yield": 2.5, "heat_release": 4.2, "safety_score": 8.8},
        "FLEX": {"flame_spread": 2.1, "extinction_time": 4.5, "soot_yield": 6.2, "heat_release": 8.9, "safety_score": 4.5},
        "ACME": {"flame_spread": 4.5, "extinction_time": 7.0, "soot_yield": 3.5, "heat_release": 5.6, "safety_score": 7.8},
        "SPICE": {"flame_spread": 3.8, "extinction_time": 6.0, "soot_yield": 8.5, "heat_release": 5.0, "safety_score": 6.0},
    }

    def get_metrics(name: str):
        for key, val in exp_metrics.items():
            if key.lower() in name.lower():
                return val
        return {"flame_spread": 5.0, "extinction_time": 6.0, "soot_yield": 5.0, "heat_release": 6.0, "safety_score": 7.0}

    exp1 = get_experiment_by_id(e1) or {"name": e1, "category": "General"}
    exp2 = get_experiment_by_id(e2) or {"name": e2, "category": "General"}

    return {
        "exp1": {"name": exp1.get("name", e1), "metrics": get_metrics(exp1.get("name", e1)), "details": exp1},
        "exp2": {"name": exp2.get("name", e2), "metrics": get_metrics(exp2.get("name", e2)), "details": exp2},
    }


@app.post("/api/score")
def calculate_score(req: ScoreRequest):
    base_scores = {
        "Nomex® Blend": 85, "Teflon (PTFE)": 82, "Kapton Film": 78,
        "Silicone Composite": 75, "Epoxy Composite": 62, "PMMA (Acrylic)": 48,
        "Nylon-6": 45, "Cotton Fabric": 38, "Polyethylene": 35, "Velcro® Strips": 30,
    }

    base = base_scores.get(req.material, 50)
    if "Lunar" in req.environment:
        base -= 3
    elif "Martian" in req.environment:
        base -= 5
    elif "Deep-Space" in req.environment:
        base -= 2

    if "34%" in req.oxygen_level:
        base -= 14
    elif "30%" in req.oxygen_level:
        base -= 8
    elif "24%" in req.oxygen_level:
        base -= 4
    elif "16%" in req.oxygen_level or "18%" in req.oxygen_level:
        base += 5

    score = max(5, min(98, base))
    if score >= 75:
        risk_level = "LOW"
    elif score >= 55:
        risk_level = "MODERATE"
    elif score >= 35:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    factors = [
        f"Altered buoyant flow in {req.environment} eliminates plume ascension and modifies oxidizer transport",
        f"Atmospheric condition of {req.oxygen_level} drastically shifts the limiting oxygen index (LOI)",
        f"Microgravity flammability boundaries for {req.material} diverge from 1g terrestrial qualification standards",
    ]

    recs = (
        f"Ensure immediate electrical isolation protocols for {req.material}. "
        f"Under exploration atmospheres ({req.oxygen_level}), enforce re-testing under NASA STD-6001 Test 1. "
        f"Mandate rapid cabin ventilation cutoff procedures upon trace detection."
    )

    ranked_table = [
        {"material": "Nomex® Blend", "iss": 85, "lunar": 82, "martian": 80, "risk": "LOW"},
        {"material": "Teflon (PTFE)", "iss": 82, "lunar": 79, "martian": 77, "risk": "LOW"},
        {"material": "Kapton Film", "iss": 78, "lunar": 75, "martian": 73, "risk": "LOW"},
        {"material": "Silicone Composite", "iss": 75, "lunar": 72, "martian": 70, "risk": "MODERATE"},
        {"material": "Epoxy Composite", "iss": 62, "lunar": 58, "martian": 55, "risk": "MODERATE"},
        {"material": "PMMA (Acrylic)", "iss": 48, "lunar": 44, "martian": 42, "risk": "HIGH"},
        {"material": "Nylon-6", "iss": 45, "lunar": 41, "martian": 38, "risk": "HIGH"},
        {"material": "Cotton Fabric", "iss": 38, "lunar": 34, "martian": 30, "risk": "HIGH"},
        {"material": "Polyethylene", "iss": 35, "lunar": 31, "martian": 28, "risk": "HIGH"},
        {"material": "Velcro® Strips", "iss": 30, "lunar": 26, "martian": 22, "risk": "CRITICAL"},
    ]

    return {
        "material": req.material,
        "environment": req.environment,
        "oxygen_level": req.oxygen_level,
        "score": score,
        "risk_level": risk_level,
        "risk_color": color_for_risk(risk_level),
        "factors": factors,
        "recommendations": recs,
        "ranked_table": ranked_table,
    }


@app.get("/api/graph")
def get_graph():
    return engine.kg.get_graph_data()


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    result = engine.rag.query(req.message, top_k=TOP_K_RESULTS, stream=False)
    raw_answer = result.get("answer") or result.get("response") or "No response generated."
    answer = clean_markdown_text(str(raw_answer))
    sources = result.get("sources", [])

    return {
        "answer": answer,
        "sources": sources,
        "kg_context": result.get("kg_context", ""),
        "history": engine.memory.get_full_history()[-10:],
    }


@app.delete("/api/chat/memory")
def clear_memory():
    engine.memory.clear()
    return {"message": "Memory cleared"}


# ── Mount Static Frontend Directory ───────────────────────────────────────────
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/manifest.json")
    def serve_manifest():
        return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"))

    @app.get("/sw.js")
    def serve_sw():
        return FileResponse(os.path.join(FRONTEND_DIR, "sw.js"))


if __name__ == "__main__":
    import uvicorn
    print("[OK] Starting Flame in Freefall on http://localhost:8000 ...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

