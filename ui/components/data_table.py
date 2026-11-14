"""
Scrollable data-table component for Flame in Freefall.
"""
from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_ORANGE,
)


class DataTable(ctk.CTkScrollableFrame):
    """A simple scrollable table with alternating row colours and click callback."""

    def __init__(self, parent, on_row_click=None, **kwargs):
        defaults = dict(
            fg_color=BG_SECONDARY,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self._on_row_click = on_row_click
        self._rows_data: list[list[str]] = []
        self._row_widgets: list[ctk.CTkFrame] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def set_data(self, headers: list[str], rows: list[list[str]]):
        """Clear table and populate with *headers* + *rows*."""
        self._clear()
        self._rows_data = rows

        # Header row
        hdr_frame = ctk.CTkFrame(self, fg_color=BG_TERTIARY, corner_radius=0, height=36)
        hdr_frame.pack(fill="x", padx=0, pady=(0, 2))
        hdr_frame.pack_propagate(False)
        for col_idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                hdr_frame, text=h,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=ACCENT_ORANGE,
                anchor="w",
            )
            lbl.pack(side="left", fill="x", expand=True, padx=12, pady=4)
        self._row_widgets.append(hdr_frame)

        # Data rows
        for row_idx, row in enumerate(rows):
            bg = BG_SECONDARY if row_idx % 2 == 0 else BG_PRIMARY
            row_frame = ctk.CTkFrame(self, fg_color=bg, corner_radius=0, height=34)
            row_frame.pack(fill="x", padx=0, pady=0)
            row_frame.pack_propagate(False)

            for col_idx, cell in enumerate(row):
                lbl = ctk.CTkLabel(
                    row_frame, text=str(cell),
                    font=ctk.CTkFont(size=12),
                    text_color=TEXT_PRIMARY,
                    anchor="w",
                )
                lbl.pack(side="left", fill="x", expand=True, padx=12, pady=2)

            # Hover + click
            self._bind_row_events(row_frame, row_idx, row)
            self._row_widgets.append(row_frame)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _bind_row_events(self, frame, row_idx, row_data):
        original_bg = BG_SECONDARY if row_idx % 2 == 0 else BG_PRIMARY

        def on_enter(e):
            frame.configure(fg_color=BG_TERTIARY)

        def on_leave(e):
            frame.configure(fg_color=original_bg)

        def on_click(e):
            if self._on_row_click:
                self._on_row_click(row_idx, row_data)

        for widget in [frame] + list(frame.winfo_children()):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def _clear(self):
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()
        self._rows_data.clear()
