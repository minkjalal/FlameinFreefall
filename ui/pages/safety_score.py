"""
Fire Safety Risk Scorer page for Flame in Freefall.
"""
from __future__ import annotations

import threading
import time
import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label, styled_button,
)
from ui.components.chart_widget import ChartWidget
from ui.components.data_table import DataTable

# ── Materials database (sample) ───────────────────────────────────────────────
MATERIALS = [
    "Cotton Fabric", "Nomex® Blend", "PMMA (Acrylic)", "Silicone Composite",
    "Polyethylene", "Teflon (PTFE)", "Kapton Film", "Velcro® Strips",
    "Nylon-6", "Epoxy Composite",
]

ENVIRONMENTS = ["ISS (LEO)", "Lunar Habitat", "Martian Habitat", "Deep-Space Transit"]

O2_OPTIONS = ["16%", "18%", "20.9% (Standard)", "24%", "30%", "34% (Exploration)"]

# Pre-computed sample safety scores
SAMPLE_SCORES = {
    ("Cotton Fabric", "ISS (LEO)", "20.9% (Standard)"): {
        "score": 38, "risk": "HIGH",
        "factors": ["High flammability in normal air", "No self-extinguishing property in µg",
                    "Commonly found in crew clothing"],
        "recs": "Replace with Nomex® blends in high-risk areas. Store in sealed containers. "
                "Ensure nearby fire suppression is operational.",
    },
    ("Nomex® Blend", "ISS (LEO)", "20.9% (Standard)"): {
        "score": 85, "risk": "LOW",
        "factors": ["Inherently flame-resistant", "Self-extinguishing even in µg",
                    "Tested extensively on ISS"],
        "recs": "Approved for general use. Periodic inspection for material degradation recommended.",
    },
}

# Ranked table data
RANKED_TABLE_HEADERS = ["Material", "ISS", "Lunar", "Martian", "Risk Level"]
RANKED_TABLE_ROWS = [
    ["Nomex® Blend", "85", "82", "80", "LOW"],
    ["Teflon (PTFE)", "82", "79", "77", "LOW"],
    ["Kapton Film", "78", "75", "73", "LOW"],
    ["Silicone Composite", "75", "72", "70", "MODERATE"],
    ["Epoxy Composite", "62", "58", "55", "MODERATE"],
    ["PMMA (Acrylic)", "48", "44", "42", "HIGH"],
    ["Nylon-6", "45", "41", "38", "HIGH"],
    ["Cotton Fabric", "38", "34", "30", "HIGH"],
    ["Polyethylene", "35", "31", "28", "HIGH"],
    ["Velcro® Strips", "30", "26", "22", "CRITICAL"],
]


class SafetyScorePage(ctk.CTkFrame):
    """Fire-safety risk scoring UI."""

    def __init__(self, parent, rag_pipeline=None, knowledge_graph=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._rag = rag_pipeline
        self._kg = knowledge_graph
        self._build_ui()

    def _build_ui(self):
        wrapper = ctk.CTkScrollableFrame(
            self, fg_color=BG_PRIMARY,
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        wrapper.pack(fill="both", expand=True)

        # Title
        styled_label(wrapper, text="🛡️ Fire Safety Risk Scorer", size=20,
                     weight="bold").pack(anchor="w", padx=24, pady=(16, 4))
        styled_label(wrapper, text="Assess material flammability risk for space environments",
                     size=13, color=TEXT_SECONDARY).pack(anchor="w", padx=24, pady=(0, 10))

        # ── Input section ─────────────────────────────────────────────────────
        input_card = styled_card(wrapper)
        input_card.pack(fill="x", padx=24, pady=6)

        input_inner = ctk.CTkFrame(input_card, fg_color="transparent")
        input_inner.pack(fill="x", padx=16, pady=14)
        input_inner.columnconfigure((0, 1, 2, 3), weight=1)

        # Material
        styled_label(input_inner, text="Material", size=12, color=TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=6)
        self._mat_var = ctk.StringVar(value=MATERIALS[0])
        ctk.CTkOptionMenu(
            input_inner, values=MATERIALS, variable=self._mat_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=4)

        # Environment
        styled_label(input_inner, text="Environment", size=12, color=TEXT_SECONDARY).grid(
            row=0, column=1, sticky="w", padx=6)
        self._env_var = ctk.StringVar(value=ENVIRONMENTS[0])
        ctk.CTkOptionMenu(
            input_inner, values=ENVIRONMENTS, variable=self._env_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
        ).grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        # O₂
        styled_label(input_inner, text="O₂ Concentration", size=12, color=TEXT_SECONDARY).grid(
            row=0, column=2, sticky="w", padx=6)
        self._o2_var = ctk.StringVar(value=O2_OPTIONS[2])
        ctk.CTkOptionMenu(
            input_inner, values=O2_OPTIONS, variable=self._o2_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
        ).grid(row=1, column=2, sticky="ew", padx=6, pady=4)

        # Button
        styled_button(
            input_inner, text="🔍 Analyse Risk", command=self._run_analysis,
            width=160, height=38,
        ).grid(row=1, column=3, padx=6, pady=4)

        # ── Results area ──────────────────────────────────────────────────────
        self._results_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        self._results_frame.pack(fill="x", padx=24, pady=8)

        # ── Ranked table ──────────────────────────────────────────────────────
        styled_label(wrapper, text="📊 Materials Ranked by Safety Score", size=16,
                     weight="bold").pack(anchor="w", padx=28, pady=(16, 6))

        table = DataTable(wrapper, height=300)
        table.pack(fill="x", padx=24, pady=(0, 20))
        table.set_data(RANKED_TABLE_HEADERS, RANKED_TABLE_ROWS)

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _run_analysis(self):
        for w in list(self._results_frame.winfo_children()):
            w.destroy()

        loading = styled_label(self._results_frame, text="⏳ Analysing risk…",
                               size=14, color=ACCENT_ORANGE)
        loading.pack(pady=12)

        threading.Thread(target=self._analyse_thread, daemon=True).start()

    def _analyse_thread(self):
        mat = self._mat_var.get()
        env = self._env_var.get()
        o2 = self._o2_var.get()

        result = None
        # Try core engine first
        if self._rag and self._kg:
            try:
                safety = self._kg.get_safety_implications(mat)
                query = f"Fire safety risk of {mat} in {env} at {o2} O₂"
                ai_result = self._rag.query(query)
                score = safety.get("score", 50) if isinstance(safety, dict) else 50
                result = {
                    "score": score,
                    "risk": self._risk_level(score),
                    "factors": safety.get("factors", []) if isinstance(safety, dict) else [],
                    "recs": str(ai_result.get("answer", ai_result) if isinstance(ai_result, dict) else ai_result),
                }
            except Exception:
                pass

        if not result:
            # Fallback to sample or generated data
            key = (mat, env, o2)
            result = SAMPLE_SCORES.get(key) or self._generate_sample(mat, env, o2)
            time.sleep(0.8)

        self.after(0, self._show_results, result)

    def _show_results(self, result: dict):
        for w in list(self._results_frame.winfo_children()):
            w.destroy()

        self._results_frame.columnconfigure((0, 1), weight=1)

        # ── Score gauge card ──────────────────────────────────────────────────
        gauge_card = styled_card(self._results_frame)
        gauge_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        score = result["score"]
        risk = result["risk"]
        color = self._risk_color(risk)

        gauge_inner = ctk.CTkFrame(gauge_card, fg_color="transparent")
        gauge_inner.pack(expand=True, padx=20, pady=20)

        styled_label(gauge_inner, text="Risk Score", size=14, color=TEXT_SECONDARY).pack()
        styled_label(gauge_inner, text=str(score), size=56, weight="bold", color=color).pack(pady=(4, 2))
        styled_label(gauge_inner, text=f"/ 100", size=14, color=TEXT_MUTED).pack()

        risk_badge = ctk.CTkFrame(gauge_inner, fg_color=color, corner_radius=8)
        risk_badge.pack(pady=10)
        styled_label(risk_badge, text=f"  {risk} RISK  ", size=14, weight="bold",
                     color=TEXT_PRIMARY).pack(padx=12, pady=6)

        # Progress bar
        bar_bg = ctk.CTkFrame(gauge_inner, fg_color=BG_TERTIARY, corner_radius=6, height=14)
        bar_bg.pack(fill="x", pady=8)
        bar_bg.pack_propagate(False)
        bar_fill = ctk.CTkFrame(bar_bg, fg_color=color, corner_radius=6)
        bar_fill.place(relx=0, rely=0, relwidth=score / 100, relheight=1)

        # ── Factors + recommendations card ────────────────────────────────────
        info_card = styled_card(self._results_frame)
        info_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="both", expand=True, padx=16, pady=14)

        styled_label(info_inner, text="⚠️ Risk Factors", size=14, weight="bold",
                     color=ACCENT_RED).pack(anchor="w", pady=(0, 6))
        for f in result.get("factors", ["No factors available"]):
            styled_label(info_inner, text=f"  • {f}", size=12, color=TEXT_SECONDARY,
                         wraplength=320).pack(anchor="w", pady=1)

        ctk.CTkFrame(info_inner, fg_color=BORDER, height=1).pack(fill="x", pady=10)

        styled_label(info_inner, text="💡 AI Recommendations", size=14, weight="bold",
                     color=ACCENT_GREEN).pack(anchor="w", pady=(0, 6))
        styled_label(info_inner, text=result.get("recs", "No recommendations available."),
                     size=12, color=TEXT_SECONDARY, wraplength=320).pack(anchor="w")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 80:
            return "LOW"
        if score >= 60:
            return "MODERATE"
        if score >= 40:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def _risk_color(risk: str) -> str:
        return {"LOW": ACCENT_GREEN, "MODERATE": ACCENT_BLUE,
                "HIGH": ACCENT_ORANGE, "CRITICAL": ACCENT_RED}.get(risk, TEXT_MUTED)

    @staticmethod
    def _generate_sample(mat: str, env: str, o2: str) -> dict:
        """Generate plausible sample data based on inputs."""
        import hashlib
        h = int(hashlib.md5(f"{mat}{env}{o2}".encode()).hexdigest(), 16) % 100
        # Bias: higher O₂ → lower score, lunar/martian slightly worse
        base = h
        if "30%" in o2 or "34%" in o2:
            base = max(10, base - 20)
        if "Lunar" in env or "Martian" in env:
            base = max(10, base - 8)
        if "Nomex" in mat or "Teflon" in mat or "Kapton" in mat:
            base = min(95, base + 25)
        if "Cotton" in mat or "Velcro" in mat:
            base = max(10, base - 15)
        score = max(5, min(95, base))
        risk = SafetyScorePage._risk_level(score)
        return {
            "score": score,
            "risk": risk,
            "factors": [
                f"Material: {mat} — {'low' if score >= 60 else 'high'} inherent flammability",
                f"Environment: {env} — {'standard' if 'ISS' in env else 'altered'} atmospheric conditions",
                f"O₂ concentration: {o2} — {'standard' if '20.9' in o2 else 'non-standard'} level",
            ],
            "recs": (f"{'Approved for general use.' if score >= 80 else 'Limit use to low-risk areas.'} "
                     f"Ensure fire suppression systems are accessible. "
                     f"{'Periodic inspection recommended.' if score >= 60 else 'Consider alternative materials.'}"),
        }
