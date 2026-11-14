"""
Navigation sidebar component for the Flame in Freefall application.
"""

from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    ACCENT_ORANGE,
    ACCENT_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    styled_label,
)


class Sidebar(ctk.CTkFrame):
    """Left navigation sidebar with modern icons, active state tracking, and branding."""

    NAV_ITEMS = [
        ("dashboard", "📊", "Dashboard"),
        ("chat", "🤖", "AI Chat & RAG"),
        ("explorer", "🔬", "Experiments"),
        ("compare", "⚖️", "Compare Data"),
        ("safety", "🛡️", "Safety Scorer"),
        ("graph", "🕸️", "Knowledge Graph"),
    ]

    def __init__(self, parent, on_page_select=None, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_SECONDARY,
            width=230,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self.pack_propagate(False)
        self._on_page_select = on_page_select
        self._active_page = "dashboard"
        self._buttons: dict[str, ctk.CTkButton] = {}

        self._build_ui()

    def _build_ui(self):
        # ── App Header / Branding ─────────────────────────────────────────────
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 16))

        logo_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_row.pack(fill="x")

        flame_icon = ctk.CTkLabel(
            logo_row,
            text="🔥",
            font=("Segoe UI Emoji", 26),
        )
        flame_icon.pack(side="left")

        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left", padx=(10, 0))

        title_lbl = ctk.CTkLabel(
            title_col,
            text="Flame in Freefall",
            font=("Segoe UI", 15, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_col,
            text="NASA Space Apps 2026",
            font=("Segoe UI", 10),
            text_color=ACCENT_ORANGE,
        )
        sub_lbl.pack(anchor="w")

        # Divider
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1)
        sep.pack(fill="x", padx=16, pady=(0, 16))

        # ── Navigation Buttons ────────────────────────────────────────────────
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=12)

        for page_id, icon, label in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_container,
                text=f"  {icon}  {label}",
                anchor="w",
                font=("Segoe UI", 13),
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=BG_TERTIARY,
                command=lambda p=page_id: self._select_page(p),
            )
            btn.pack(fill="x", pady=3)
            self._buttons[page_id] = btn

        self._update_button_styles()

        # ── Bottom Status Card ────────────────────────────────────────────────
        bottom_frame = ctk.CTkFrame(
            self,
            fg_color=BG_PRIMARY,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        bottom_frame.pack(fill="x", padx=12, pady=16)

        status_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=10, pady=8)

        dot = ctk.CTkLabel(status_row, text="●", text_color="#22c55e", font=("Segoe UI", 12))
        dot.pack(side="left")

        team_label = ctk.CTkLabel(
            status_row,
            text="Team Eagle20",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_PRIMARY,
        )
        team_label.pack(side="left", padx=6)

        info_lbl = ctk.CTkLabel(
            bottom_frame,
            text="Haldwani Local Event\nMicrogravity Combustion RAG",
            font=("Segoe UI", 9),
            text_color=TEXT_MUTED,
            justify="left",
        )
        info_lbl.pack(anchor="w", padx=10, pady=(0, 8))

    def _select_page(self, page_id: str):
        if self._active_page == page_id:
            return
        self._active_page = page_id
        self._update_button_styles()
        if self._on_page_select:
            self._on_page_select(page_id)

    def _update_button_styles(self):
        for pid, btn in self._buttons.items():
            if pid == self._active_page:
                btn.configure(
                    fg_color=BG_TERTIARY,
                    text_color=ACCENT_ORANGE,
                    font=("Segoe UI", 13, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    font=("Segoe UI", 13, "normal"),
                )

    def set_active(self, page_id: str):
        """Programmatically switch active button."""
        if page_id in self._buttons:
            self._active_page = page_id
            self._update_button_styles()
