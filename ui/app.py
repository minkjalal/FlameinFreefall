"""
Main application window for the Flame in Freefall dashboard.
Optimized for instant (<1s) startup with lazy-loaded pages and non-blocking background RAG.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import customtkinter as ctk

# Ensure fast font resolution
try:
    import matplotlib
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
except Exception:
    pass

# Optional drag-and-drop
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from config import (
    APP_HEIGHT,
    APP_TITLE,
    APP_WIDTH,
    THEME_MODE,
)
from core.gemini_client import GeminiClient
from core.ingestion import load_and_chunk_data
from core.knowledge_graph import KnowledgeGraph
from core.memory import ConversationMemory
from core.rag_pipeline import RAGPipeline
from core.vectorstore import VectorStore
from ui.pages.chat import ChatPage
from ui.pages.compare import ComparePage
from ui.pages.dashboard import DashboardPage
from ui.pages.explorer import ExplorerPage
from ui.pages.graph_view import GraphViewPage
from ui.pages.safety_score import SafetyScorePage
from ui.sidebar import Sidebar
from ui.themes.space_theme import (
    BG_PRIMARY,
    BG_SECONDARY,
    BORDER,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from utils.data_loader import load_all_data

logger = logging.getLogger(__name__)


if HAS_DND:
    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:
                pass
else:
    class BaseWindow(ctk.CTk):
        pass


class DataManager:
    """Provides statistics to DashboardPage."""

    def __init__(self, data: dict[str, list[dict]]):
        self.data = data

    def get_stats(self) -> dict[str, int]:
        return {
            "total_experiments": len(self.data.get("experiments", [])),
            "materials_tested": len(self.data.get("materials", [])),
            "key_findings": len(self.data.get("findings", [])),
            "safety_scores": len(self.data.get("guidelines", [])),
        }


class FlameApp(BaseWindow):
    """Main application orchestrator with lazy page loading."""

    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode(THEME_MODE)
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(1050, 680)
        self.configure(fg_color=BG_PRIMARY)

        # Core engine state
        self._all_data: dict[str, list[dict]] = {}
        self._gemini: GeminiClient | None = None
        self._memory: ConversationMemory | None = None
        self._vectorstore: VectorStore | None = None
        self._kg: KnowledgeGraph | None = None
        self._rag: RAGPipeline | None = None
        self._data_manager: DataManager | None = None

        # UI state - pages created on-demand for lightning fast startup
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._active_page_id: str = "dashboard"

        self._build_shell()
        self._show_page("dashboard")
        self._init_background_engine()

    def _build_shell(self):
        """Construct sidebar, container, and status bar."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Status bar
        self.grid_columnconfigure(0, weight=0)  # Sidebar (fixed)
        self.grid_columnconfigure(1, weight=1)  # Content (expands)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = Sidebar(self, on_page_select=self.switch_page)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main Content Container ────────────────────────────────────────────
        self._container = ctk.CTkFrame(self, fg_color=BG_PRIMARY, corner_radius=0)
        self._container.grid(row=0, column=1, sticky="nsew")

        # ── Status Bar ────────────────────────────────────────────────────────
        self._status_bar = ctk.CTkFrame(
            self,
            fg_color=BG_SECONDARY,
            height=28,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self._status_lbl = ctk.CTkLabel(
            self._status_bar,
            text="⚡ Initializing NASA Combustion RAG Pipeline & Knowledge Graph…",
            font=("Segoe UI", 10),
            text_color=TEXT_MUTED,
        )
        self._status_lbl.pack(side="left", padx=16, pady=2)

        self._engine_status_lbl = ctk.CTkLabel(
            self._status_bar,
            text="Core Engine: Ingesting Data",
            font=("Segoe UI", 10, "bold"),
            text_color=TEXT_SECONDARY,
        )
        self._engine_status_lbl.pack(side="right", padx=16, pady=2)

    def switch_page(self, page_id: str):
        """Switch active page, creating it lazily if not yet created."""
        self._show_page(page_id)

    def _show_page(self, page_id: str):
        """Display the requested page using clean pack/pack_forget."""
        # Hide current page if any
        if self._active_page_id in self._pages:
            self._pages[self._active_page_id].pack_forget()

        # Create page on demand if not yet cached
        if page_id not in self._pages:
            self._pages[page_id] = self._create_page(page_id)

        # Show active page
        self._pages[page_id].pack(fill="both", expand=True)
        self._active_page_id = page_id
        self._sidebar.set_active(page_id)

    def _create_page(self, page_id: str) -> ctk.CTkFrame:
        """Instantiate a page with current engine data."""
        exp_list = self._all_data.get("experiments", [])

        if page_id == "dashboard":
            return DashboardPage(self._container, data_manager=self._data_manager)

        elif page_id == "chat":
            return ChatPage(self._container, rag_pipeline=self._rag)

        elif page_id == "explorer":
            return ExplorerPage(self._container, experiments=exp_list if exp_list else None)

        elif page_id == "compare":
            compare_list = self._build_compare_list()
            return ComparePage(self._container, experiments=compare_list if compare_list else None)

        elif page_id == "safety":
            return SafetyScorePage(
                self._container, rag_pipeline=self._rag, knowledge_graph=self._kg
            )

        elif page_id == "graph":
            return GraphViewPage(self._container, knowledge_graph=self._kg)

        return DashboardPage(self._container)

    def _build_compare_list(self) -> list[dict]:
        exp_list = self._all_data.get("experiments", [])
        compare_list = []
        for exp in exp_list:
            compare_list.append({
                "name": exp.get("name", "Unknown"),
                "category": exp.get("category", "General"),
                "material": ", ".join(exp.get("materials_tested", []))[:30] or "Standard Sample",
                "o2_range": f"{exp.get('parameters', {}).get('oxygen_concentration', {}).get('min', 18)}-{exp.get('parameters', {}).get('oxygen_concentration', {}).get('max', 24)}%",
                "pressure": "14.7 psia",
                "flame_spread": 5.5,
                "extinction_time": 65,
                "soot_yield": 4.0,
                "heat_release": 6.8,
                "safety_score": 75,
            })
        return compare_list

    # ── Background Engine Initialization ──────────────────────────────────────

    def _init_background_engine(self):
        """Initialize data loading, vector indexing, and RAG in a worker thread."""
        thread = threading.Thread(target=self._run_engine_init, daemon=True)
        thread.start()

    def _run_engine_init(self):
        try:
            # 1. Load structured JSON data
            self._all_data = load_all_data()
            self._data_manager = DataManager(self._all_data)

            # 2. Build Knowledge Graph
            self._kg = KnowledgeGraph()
            experiments = self._all_data.get("experiments", [])
            self._kg.build_from_data(experiments)

            # 3. Vector store & ingestion
            self._vectorstore = VectorStore()
            chunks = load_and_chunk_data()
            if self._vectorstore.get_collection_stats().get("document_count", 0) == 0 and chunks:
                self._vectorstore.add_documents(chunks)

            # 4. Gemini client & Memory
            self._gemini = GeminiClient()
            self._memory = ConversationMemory()

            # 5. RAG Pipeline
            self._rag = RAGPipeline(
                vectorstore=self._vectorstore,
                knowledge_graph=self._kg,
                gemini_client=self._gemini,
                memory=self._memory,
            )

            # Update UI on main thread safely
            try:
                self.after(0, self._on_engine_ready)
            except Exception:
                pass

        except Exception as e:
            logger.error("Failed to initialize engine: %s", e, exc_info=True)
            try:
                self.after(0, lambda: self._on_engine_failed(str(e)))
            except Exception:
                pass

    def _on_engine_ready(self):
        """Update status bar and inject RAG into existing pages without destroying them."""
        try:
            # If chat page is already opened, attach RAG pipeline
            if "chat" in self._pages and hasattr(self._pages["chat"], "_rag"):
                self._pages["chat"]._rag = self._rag

            # If safety page is already opened, attach RAG and KG
            if "safety" in self._pages:
                self._pages["safety"]._rag = self._rag
                self._pages["safety"]._kg = self._kg

            # If graph page is already opened, attach KG
            if "graph" in self._pages:
                self._pages["graph"]._kg = self._kg

            exp_count = len(self._all_data.get("experiments", []))
            mat_count = len(self._all_data.get("materials", []))
            find_count = len(self._all_data.get("findings", []))

            self._status_lbl.configure(
                text=f"🟢 Grounded RAG Active • {exp_count} NASA Experiments • {mat_count} Materials • {find_count} Findings Ingested",
                text_color="#22c55e",
            )
            mode = "Gemini 2.5 Live" if (self._gemini and self._gemini.is_configured) else "Local Knowledge RAG"
            self._engine_status_lbl.configure(text=f"Engine: {mode}", text_color=TEXT_PRIMARY)

        except Exception as e:
            logger.error("Error updating pages with live engine: %s", e)

    def _on_engine_failed(self, error_msg: str):
        self._status_lbl.configure(
            text=f"⚠️ Engine running with fallback cache ({error_msg[:60]}…)",
            text_color="#eab308",
        )
        self._engine_status_lbl.configure(text="Engine: Safe Mode", text_color="#ef4444")
