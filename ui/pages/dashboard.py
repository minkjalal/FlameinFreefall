"""
Dashboard page – overview of microgravity combustion research data.
"""
from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label,
)
from ui.components.chart_widget import ChartWidget

# ── Sample / fallback data ────────────────────────────────────────────────────
SAMPLE_STATS = {
    "total_experiments": 156,
    "materials_tested": 42,
    "key_findings": 89,
    "safety_scores": 34,
}

SAMPLE_CATEGORIES = {
    "BASS": 28, "ACME": 22, "SAFFIRE": 18,
    "SoFIE": 15, "FLEX": 24, "SPICE": 12,
    "CFS": 9, "Other": 28,
}

SAMPLE_MATERIALS = {
    "Polymers": 35, "Fabrics": 22, "Metals": 15,
    "Composites": 18, "Foams": 10,
}

SAMPLE_FINDINGS = [
    ("🔬", "SAFFIRE-IV", "Large-scale fire growth rates in microgravity confirmed to be 2-3× slower than predicted models."),
    ("⚡", "BASS-II", "Flame spread over thin PMMA samples shows strong dependence on ambient oxygen concentration."),
    ("🧪", "SoFIE-GEL", "Gel-based fire suppressants demonstrate 40% faster extinction in microgravity environments."),
    ("🔥", "FLEX-2", "Cool-flame burning regime discovered — sustains combustion below standard flammability limits."),
    ("🛡️", "ACME-03", "Modified cotton-Nomex blends show improved fire resistance under reduced-gravity conditions."),
    ("📊", "SPICE", "Smoke-point measurements in co-flow reveal increased soot formation at low flow velocities."),
    ("🚀", "CFS-1", "Spacecraft cabin ventilation flow strongly influences flame attachment and spread direction."),
]


class DashboardPage(ctk.CTkFrame):
    """Main dashboard with stat cards, charts, and recent findings."""

    def __init__(self, parent, data_manager=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._dm = data_manager
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Scrollable wrapper so content doesn't clip on smaller screens
        wrapper = ctk.CTkScrollableFrame(
            self, fg_color=BG_PRIMARY,
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        wrapper.pack(fill="both", expand=True, padx=0, pady=0)

        # Page title
        title_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        title_frame.pack(fill="x", padx=24, pady=(20, 4))
        styled_label(title_frame, text="🔥 Mission Dashboard", size=22, weight="bold").pack(side="left")
        styled_label(title_frame, text="Real-time overview of microgravity combustion research",
                     size=13, color=TEXT_SECONDARY).pack(side="left", padx=16)

        # ── Stat cards row ────────────────────────────────────────────────────
        stats = self._get_stats()
        cards_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=(12, 8))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        card_defs = [
            ("🧪", "Total Experiments", stats["total_experiments"], "Across all NASA programmes", ACCENT_ORANGE),
            ("🧬", "Materials Tested", stats["materials_tested"], "Unique sample materials", ACCENT_BLUE),
            ("💡", "Key Findings", stats["key_findings"], "Published research insights", ACCENT_GREEN),
            ("🛡️", "Safety Scores", stats["safety_scores"], "Risk assessments completed", ACCENT_RED),
        ]
        for col, (emoji, title, value, subtitle, accent) in enumerate(card_defs):
            self._make_stat_card(cards_frame, emoji, title, value, subtitle, accent, col)

        # ── Charts row ────────────────────────────────────────────────────────
        charts_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        charts_frame.pack(fill="x", padx=24, pady=8)
        charts_frame.columnconfigure((0, 1), weight=1)

        bar_chart = ChartWidget(charts_frame, figsize=(5, 3))
        bar_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        bar_chart.plot_bar(SAMPLE_CATEGORIES, title="Experiments by Category")

        pie_chart = ChartWidget(charts_frame, figsize=(5, 3))
        pie_chart.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)
        pie_chart.plot_pie(SAMPLE_MATERIALS, title="Material Types Studied")

        # ── Recent findings ───────────────────────────────────────────────────
        findings_label = styled_label(wrapper, text="📋 Recent Findings", size=17, weight="bold")
        findings_label.pack(anchor="w", padx=28, pady=(16, 6))

        findings_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        findings_frame.pack(fill="x", padx=24, pady=(0, 20))

        for emoji, experiment, description in SAMPLE_FINDINGS:
            self._make_finding_row(findings_frame, emoji, experiment, description)

    # ── Widget builders ───────────────────────────────────────────────────────

    def _make_stat_card(self, parent, emoji, title, value, subtitle, accent, col):
        card = styled_card(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=emoji, font=ctk.CTkFont(size=24)).pack(side="left")
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=13),
                     text_color=TEXT_SECONDARY).pack(side="left", padx=8)

        ctk.CTkLabel(inner, text=str(value), font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=accent).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(inner, text=subtitle, font=ctk.CTkFont(size=11),
                     text_color=TEXT_MUTED).pack(anchor="w")

    def _make_finding_row(self, parent, emoji, experiment, description):
        row = styled_card(parent)
        row.pack(fill="x", padx=0, pady=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(inner, text=emoji, font=ctk.CTkFont(size=18), width=28).pack(side="left")
        ctk.CTkLabel(inner, text=experiment, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=ACCENT_ORANGE, width=100, anchor="w").pack(side="left", padx=(6, 12))
        ctk.CTkLabel(inner, text=description, font=ctk.CTkFont(size=12),
                     text_color=TEXT_SECONDARY, anchor="w", wraplength=700).pack(side="left", fill="x", expand=True)

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _get_stats(self) -> dict:
        if self._dm:
            try:
                return self._dm.get_stats()
            except Exception:
                pass
        return SAMPLE_STATS
