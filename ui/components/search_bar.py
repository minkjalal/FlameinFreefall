"""
Reusable search-bar component for Flame in Freefall.
"""
import customtkinter as ctk

from ui.themes.space_theme import (
    BG_SECONDARY, BG_TERTIARY, BORDER, ACCENT_ORANGE,
    TEXT_PRIMARY, TEXT_MUTED, styled_button,
)


class SearchBar(ctk.CTkFrame):
    """A search bar with an entry field and search button."""

    def __init__(
        self,
        parent,
        placeholder: str = "Search experiments…",
        on_search=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search

        # Container
        self._container = ctk.CTkFrame(
            self, fg_color=BG_SECONDARY, corner_radius=10,
            border_width=1, border_color=BORDER,
        )
        self._container.pack(fill="x", padx=0, pady=0)

        # Search icon label
        self._icon = ctk.CTkLabel(
            self._container, text="🔍", font=ctk.CTkFont(size=16),
            text_color=TEXT_MUTED, width=32,
        )
        self._icon.pack(side="left", padx=(12, 0), pady=8)

        # Entry
        self._entry = ctk.CTkEntry(
            self._container,
            placeholder_text=placeholder,
            fg_color=BG_TERTIARY,
            border_width=0,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            height=36,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        self._entry.bind("<Return>", lambda e: self._fire_search())

        # Button
        self._btn = styled_button(
            self._container, text="Search", command=self._fire_search,
            height=36, width=90, corner_radius=8,
        )
        self._btn.pack(side="right", padx=(0, 8), pady=8)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_query(self) -> str:
        return self._entry.get().strip()

    def clear(self):
        self._entry.delete(0, "end")

    def set_text(self, text: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, text)

    # ── Private ───────────────────────────────────────────────────────────────

    def _fire_search(self):
        query = self.get_query()
        if query and self._on_search:
            self._on_search(query)
