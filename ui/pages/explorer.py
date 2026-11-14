"""
Experiment Explorer page for Flame in Freefall.
"""
from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label, styled_button,
)
from ui.components.search_bar import SearchBar

# ── Sample experiment data ────────────────────────────────────────────────────
SAMPLE_EXPERIMENTS = [
    {
        "name": "SAFFIRE-IV",
        "category": "Large-Scale Fire",
        "material": "Cotton-Fibreglass Blend",
        "description": "Large-scale fire growth & behaviour aboard Cygnus NG-14.",
        "o2_range": "21%",
        "pressure": "14.7 psia",
        "gravity": "Microgravity",
        "status": "Completed",
        "findings": "Fire growth rates 2-3× slower than Earth models predict.",
    },
    {
        "name": "BASS-II",
        "category": "Flame Spread",
        "material": "PMMA (Acrylic)",
        "description": "Burning and suppression of solid fuels in microgravity.",
        "o2_range": "15-24%",
        "pressure": "14.7 psia",
        "gravity": "Microgravity",
        "status": "Completed",
        "findings": "Flame spread rate depends strongly on oxygen concentration.",
    },
    {
        "name": "SoFIE-GEL",
        "category": "Suppression",
        "material": "Silicone Composite",
        "description": "Solid fuel ignition & extinction with gel suppressants.",
        "o2_range": "18-21%",
        "pressure": "14.7 psia",
        "gravity": "Microgravity",
        "status": "Active",
        "findings": "Gel suppressants 40% faster extinction in microgravity.",
    },
    {
        "name": "FLEX-2",
        "category": "Droplet Combustion",
        "material": "Heptane Droplets",
        "description": "Flame Extinguishment Experiment — droplet burning.",
        "o2_range": "21%",
        "pressure": "1 atm",
        "gravity": "Microgravity",
        "status": "Completed",
        "findings": "Discovered cool-flame regime sustaining below flammability limits.",
    },
    {
        "name": "ACME-03",
        "category": "Advanced Combustion",
        "material": "Cotton-Nomex Blend",
        "description": "Advanced Combustion via Microgravity Experiments.",
        "o2_range": "18-25%",
        "pressure": "10.2-14.7 psia",
        "gravity": "Microgravity",
        "status": "Completed",
        "findings": "Modified blends show improved fire resistance in reduced gravity.",
    },
    {
        "name": "SPICE",
        "category": "Soot & Smoke",
        "material": "Ethylene Gas",
        "description": "Smoke Point In Co-flow Experiment for soot formation.",
        "o2_range": "21%",
        "pressure": "1 atm",
        "gravity": "Microgravity",
        "status": "Completed",
        "findings": "Increased soot formation at low flow velocities in 0g.",
    },
    {
        "name": "CFS-1",
        "category": "Cabin Flow",
        "material": "Nomex® Fabric",
        "description": "Cabin ventilation impact on flame spread & attachment.",
        "o2_range": "20.9%",
        "pressure": "14.7 psia",
        "gravity": "Microgravity",
        "status": "Active",
        "findings": "Ventilation flow strongly influences flame direction.",
    },
    {
        "name": "SAFFIRE-VI",
        "category": "Large-Scale Fire",
        "material": "Composite Panel",
        "description": "Testing composite spacecraft panels at large scale.",
        "o2_range": "21-34%",
        "pressure": "8.2-14.7 psia",
        "gravity": "Microgravity",
        "status": "Planned",
        "findings": "Expected to validate new composite fire barriers.",
    },
]

STATUS_COLORS = {
    "Completed": ACCENT_GREEN,
    "Active": ACCENT_BLUE,
    "Planned": ACCENT_ORANGE,
}


class ExplorerPage(ctk.CTkFrame):
    """Experiment explorer with filters, search, and expandable cards."""

    def __init__(self, parent, experiments=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._experiments = experiments or SAMPLE_EXPERIMENTS
        self._filtered = list(self._experiments)
        self._detail_popup = None
        self._build_ui()
        self._render_cards()

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(16, 6))

        styled_label(top, text="🔬 Experiment Explorer", size=20, weight="bold").pack(side="left")

        search = SearchBar(top, placeholder="Search experiments…", on_search=self._on_search)
        search.pack(side="right", fill="x", expand=True, padx=(20, 0))

        # ── Body = sidebar + grid ─────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=0, pady=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Left filter sidebar ───────────────────────────────────────────────
        sidebar = ctk.CTkFrame(body, fg_color=BG_SECONDARY, corner_radius=12,
                               border_width=1, border_color=BORDER, width=210)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(20, 8), pady=10)
        sidebar.pack_propagate(False)

        styled_label(sidebar, text="🎛️ Filters", size=15, weight="bold").pack(
            anchor="w", padx=14, pady=(14, 10))

        # Category
        styled_label(sidebar, text="Category", size=12, color=TEXT_SECONDARY).pack(
            anchor="w", padx=14, pady=(6, 2))
        categories = sorted({e.get("category", "General") for e in self._experiments})
        self._cat_var = ctk.StringVar(value="All")
        cat_menu = ctk.CTkOptionMenu(
            sidebar, values=["All"] + categories, variable=self._cat_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
            command=lambda _: self._apply_filters(),
        )
        cat_menu.pack(padx=14, pady=4)

        # Material
        styled_label(sidebar, text="Material", size=12, color=TEXT_SECONDARY).pack(
            anchor="w", padx=14, pady=(10, 2))
        mat_set = set()
        for e in self._experiments:
            m = e.get("material")
            if m:
                mat_set.add(str(m))
            for mt in e.get("materials_tested", []):
                mat_set.add(str(mt))
        materials = sorted(mat_set) if mat_set else ["Standard Samples"]
        self._mat_var = ctk.StringVar(value="All")
        mat_menu = ctk.CTkOptionMenu(
            sidebar, values=["All"] + materials[:20], variable=self._mat_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
            command=lambda _: self._apply_filters(),
        )
        mat_menu.pack(padx=14, pady=4)

        # Status
        styled_label(sidebar, text="Status", size=12, color=TEXT_SECONDARY).pack(
            anchor="w", padx=14, pady=(10, 2))
        self._status_var = ctk.StringVar(value="All")
        status_menu = ctk.CTkOptionMenu(
            sidebar, values=["All", "Completed", "Active", "Planned"],
            variable=self._status_var,
            fg_color=BG_TERTIARY, button_color=ACCENT_ORANGE,
            button_hover_color="#e06510", text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_TERTIARY, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=ACCENT_ORANGE, width=180,
            command=lambda _: self._apply_filters(),
        )
        status_menu.pack(padx=14, pady=4)

        # Reset
        styled_button(sidebar, text="Reset Filters", command=self._reset_filters,
                      accent=BG_TERTIARY, width=180, height=34).pack(padx=14, pady=(20, 10))

        # ── Card grid ─────────────────────────────────────────────────────────
        self._grid_frame = ctk.CTkScrollableFrame(
            body, fg_color=BG_PRIMARY,
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        self._grid_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 20), pady=10)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render_cards(self):
        for w in list(self._grid_frame.winfo_children()):
            w.destroy()

        if not self._filtered:
            styled_label(self._grid_frame, text="No experiments match the filters.",
                         size=14, color=TEXT_MUTED).pack(pady=40)
            return

        # Two-column grid
        self._grid_frame.columnconfigure((0, 1), weight=1)
        for idx, exp in enumerate(self._filtered):
            row, col = divmod(idx, 2)
            card = self._make_card(self._grid_frame, exp)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

    def _make_card(self, parent, exp: dict) -> ctk.CTkFrame:
        card = styled_card(parent)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Header row
        hdr = ctk.CTkFrame(inner, fg_color="transparent")
        hdr.pack(fill="x")
        styled_label(hdr, text=exp["name"], size=15, weight="bold").pack(side="left")
        status_color = STATUS_COLORS.get(exp.get("status", ""), TEXT_MUTED)
        styled_label(hdr, text=f"● {exp.get('status', 'N/A')}", size=11,
                     color=status_color).pack(side="right")

        styled_label(inner, text=exp["category"], size=11, color=ACCENT_ORANGE).pack(
            anchor="w", pady=(4, 2))
        styled_label(inner, text=exp["description"], size=12, color=TEXT_SECONDARY,
                     wraplength=350).pack(anchor="w", pady=(2, 8))

        # Params
        params_frame = ctk.CTkFrame(inner, fg_color=BG_TERTIARY, corner_radius=8)
        params_frame.pack(fill="x", pady=(0, 6))

        mat_text = exp.get("material") or (", ".join(exp.get("materials_tested", []))[:35] if exp.get("materials_tested") else "Spacecraft Samples")
        o2_text = exp.get("o2_range") or (f"{exp.get('parameters', {}).get('oxygen_concentration', {}).get('min', 18)}-{exp.get('parameters', {}).get('oxygen_concentration', {}).get('max', 24)}%" if isinstance(exp.get("parameters"), dict) else "21% (Standard)")
        grav_text = exp.get("gravity") or exp.get("platform", "Microgravity")

        for label, val in [("Material", mat_text), ("O₂", o2_text), ("Platform", grav_text)]:
            pf = ctk.CTkFrame(params_frame, fg_color="transparent")
            pf.pack(fill="x", padx=10, pady=2)
            styled_label(pf, text=f"{label}:", size=11, color=TEXT_MUTED).pack(side="left")
            styled_label(pf, text=str(val), size=11, color=TEXT_PRIMARY).pack(side="left", padx=6)

        # View details
        styled_button(inner, text="View Details →", command=lambda e=exp: self._show_details(e),
                      height=30, width=130, accent=BG_TERTIARY).pack(anchor="e")

        return card

    def _show_details(self, exp: dict):
        if self._detail_popup and self._detail_popup.winfo_exists():
            self._detail_popup.destroy()

        self._detail_popup = ctk.CTkToplevel(self)
        self._detail_popup.title(exp["name"])
        self._detail_popup.geometry("500x420")
        self._detail_popup.configure(fg_color=BG_PRIMARY)

        styled_label(self._detail_popup, text=f"🔬 {exp['name']}", size=20,
                     weight="bold").pack(anchor="w", padx=20, pady=(16, 4))
        styled_label(self._detail_popup, text=exp["category"], size=13,
                     color=ACCENT_ORANGE).pack(anchor="w", padx=20)

        ctk.CTkFrame(self._detail_popup, fg_color=BORDER, height=1).pack(fill="x", padx=20, pady=10)

        for label, key in [("Description", "description"), ("Material", "material"),
                           ("O₂ Range", "o2_range"), ("Pressure", "pressure"),
                           ("Gravity", "gravity"), ("Status", "status"),
                           ("Key Findings", "findings")]:
            row = ctk.CTkFrame(self._detail_popup, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            styled_label(row, text=f"{label}:", size=12, weight="bold",
                         color=ACCENT_BLUE).pack(side="left")
            styled_label(row, text=exp.get(key, "N/A"), size=12, color=TEXT_PRIMARY,
                         wraplength=350).pack(side="left", padx=8)

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _on_search(self, query: str):
        q = query.lower()
        self._filtered = [
            e for e in self._experiments
            if q in e.get("name", "").lower()
            or q in e.get("description", "").lower()
            or q in e.get("material", "").lower()
            or any(q in m.lower() for m in e.get("materials_tested", []))
        ]
        self._render_cards()

    def _apply_filters(self):
        cat = self._cat_var.get()
        mat = self._mat_var.get()
        status = self._status_var.get()

        def _match_mat(e):
            if mat == "All":
                return True
            if e.get("material") == mat:
                return True
            for m in e.get("materials_tested", []):
                if mat in m or m in mat:
                    return True
            return False

        self._filtered = [
            e for e in self._experiments
            if (cat == "All" or e.get("category", "General") == cat)
            and _match_mat(e)
            and (status == "All" or e.get("status", "Completed") == status)
        ]
        self._render_cards()

    def _reset_filters(self):
        self._cat_var.set("All")
        self._mat_var.set("All")
        self._status_var.set("All")
        self._filtered = list(self._experiments)
        self._render_cards()
