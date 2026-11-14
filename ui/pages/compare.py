"""
Side-by-side experiment comparison page for Flame in Freefall.
"""
from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label,
)
from ui.components.chart_widget import ChartWidget

# ── Sample experiment data ────────────────────────────────────────────────────
SAMPLE_EXPERIMENTS = [
    {
        "name": "SAFFIRE-IV",
        "category": "Large-Scale Fire",
        "material": "Cotton-Fibreglass Blend",
        "o2_range": "21%",
        "pressure": "14.7 psia",
        "flame_spread": 7.2,
        "extinction_time": 85,
        "soot_yield": 3.1,
        "heat_release": 6.5,
        "safety_score": 72,
    },
    {
        "name": "BASS-II",
        "category": "Flame Spread",
        "material": "PMMA (Acrylic)",
        "o2_range": "15-24%",
        "pressure": "14.7 psia",
        "flame_spread": 5.8,
        "extinction_time": 60,
        "soot_yield": 4.5,
        "heat_release": 7.8,
        "safety_score": 65,
    },
    {
        "name": "SoFIE-GEL",
        "category": "Suppression",
        "material": "Silicone Composite",
        "o2_range": "18-21%",
        "pressure": "14.7 psia",
        "flame_spread": 3.2,
        "extinction_time": 35,
        "soot_yield": 1.8,
        "heat_release": 4.2,
        "safety_score": 88,
    },
    {
        "name": "FLEX-2",
        "category": "Droplet Combustion",
        "material": "Heptane Droplets",
        "o2_range": "21%",
        "pressure": "1 atm",
        "flame_spread": 2.1,
        "extinction_time": 120,
        "soot_yield": 6.2,
        "heat_release": 8.9,
        "safety_score": 45,
    },
    {
        "name": "ACME-03",
        "category": "Advanced Combustion",
        "material": "Cotton-Nomex Blend",
        "o2_range": "18-25%",
        "pressure": "10.2-14.7 psia",
        "flame_spread": 4.5,
        "extinction_time": 55,
        "soot_yield": 2.9,
        "heat_release": 5.6,
        "safety_score": 78,
    },
]

RADAR_KEYS = ["flame_spread", "extinction_time", "soot_yield", "heat_release", "safety_score"]
RADAR_LABELS = {
    "flame_spread": "Flame Spread",
    "extinction_time": "Extinction Time",
    "soot_yield": "Soot Yield",
    "heat_release": "Heat Release",
    "safety_score": "Safety Score",
}

# Normalise values to 0-10 for the radar
RADAR_MAX = {"flame_spread": 10, "extinction_time": 150, "soot_yield": 10,
             "heat_release": 10, "safety_score": 100}


class ComparePage(ctk.CTkFrame):
    """Side-by-side comparison of two experiments."""

    def __init__(self, parent, experiments=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._experiments = experiments or SAMPLE_EXPERIMENTS
        self._build_ui()
        # Initial comparison
        if len(self._experiments) >= 2:
            self._update_comparison()

    def _build_ui(self):
        # Title
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 6))
        styled_label(top, text="⚖️ Experiment Comparison", size=20, weight="bold").pack(side="left")

        # ── Selectors ─────────────────────────────────────────────────────────
        sel_frame = ctk.CTkFrame(self, fg_color="transparent")
        sel_frame.pack(fill="x", padx=24, pady=8)

        names = [e["name"] for e in self._experiments]

        styled_label(sel_frame, text="Experiment A:", size=13, color=TEXT_SECONDARY).pack(side="left")
        self._var_a = ctk.StringVar(value=names[0] if names else "")
        ctk.CTkOptionMenu(
            sel_frame, values=names, variable=self._var_a,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=200,
            command=lambda _: self._update_comparison(),
        ).pack(side="left", padx=(6, 24))

        styled_label(sel_frame, text="Experiment B:", size=13, color=TEXT_SECONDARY).pack(side="left")
        self._var_b = ctk.StringVar(value=names[1] if len(names) > 1 else "")
        ctk.CTkOptionMenu(
            sel_frame, values=names, variable=self._var_b,
            fg_color=BG_TERTIARY, button_color=ACCENT_BLUE,
            button_hover_color="#2563eb", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_BLUE, width=200,
            command=lambda _: self._update_comparison(),
        ).pack(side="left", padx=6)

        # ── Content area (replaced on each selection) ─────────────────────────
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=24, pady=8)

    # ── Comparison logic ──────────────────────────────────────────────────────

    def _update_comparison(self):
        for w in list(self._content.winfo_children()):
            w.destroy()

        exp_a = self._find(self._var_a.get())
        exp_b = self._find(self._var_b.get())
        if not exp_a or not exp_b:
            styled_label(self._content, text="Select two experiments above.",
                         size=14, color=TEXT_MUTED).pack(pady=40)
            return

        # ── Side-by-side cards ────────────────────────────────────────────────
        cards_row = ctk.CTkFrame(self._content, fg_color="transparent")
        cards_row.pack(fill="x", pady=6)
        cards_row.columnconfigure((0, 1), weight=1)

        self._detail_card(cards_row, exp_a, ACCENT_ORANGE, 0)
        self._detail_card(cards_row, exp_b, ACCENT_BLUE, 1)

        # ── Radar chart ───────────────────────────────────────────────────────
        radar = ChartWidget(self._content, figsize=(6, 4))
        radar.pack(fill="both", expand=True, pady=(8, 4))

        radar_data = {}
        for exp, color_label in [(exp_a, exp_a["name"]), (exp_b, exp_b["name"])]:
            radar_data[color_label] = {
                RADAR_LABELS[k]: (exp.get(k, 0) / RADAR_MAX[k]) * 10
                for k in RADAR_KEYS
            }
        radar.plot_radar(radar_data, title="Comparative Analysis")

    def _detail_card(self, parent, exp: dict, accent, col):
        card = styled_card(parent, border_color=accent)
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=0)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        styled_label(inner, text=exp["name"], size=17, weight="bold", color=accent).pack(
            anchor="w", pady=(0, 4))
        styled_label(inner, text=exp["category"], size=12, color=TEXT_SECONDARY).pack(
            anchor="w", pady=(0, 8))

        for label, key in [("Material", "material"), ("O₂ Range", "o2_range"),
                           ("Pressure", "pressure"), ("Flame Spread", "flame_spread"),
                           ("Extinction Time", "extinction_time"),
                           ("Soot Yield", "soot_yield"),
                           ("Heat Release", "heat_release"),
                           ("Safety Score", "safety_score")]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            styled_label(row, text=f"{label}:", size=12, color=TEXT_MUTED).pack(side="left")
            val = exp.get(key, "N/A")
            styled_label(row, text=str(val), size=12, color=TEXT_PRIMARY).pack(side="left", padx=8)

    def _find(self, name: str) -> dict | None:
        for e in self._experiments:
            if e["name"] == name:
                return e
        return None
