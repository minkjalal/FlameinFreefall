"""
AI Chat interface page for Flame in Freefall.
"""
from __future__ import annotations

import threading
import time
import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label, styled_button,
)
from utils.helpers import clean_markdown_text


class ChatPage(ctk.CTkFrame):
    """Full AI chat interface with message bubbles, sources panel, and threaded queries."""

    def __init__(self, parent, rag_pipeline=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._rag = rag_pipeline
        self._messages: list[dict] = []
        self._is_thinking = False
        self._typing_label = None
        self._build_ui()
        self._add_welcome()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Main horizontal split
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=0, pady=0)
        self._body.columnconfigure(0, weight=3)
        self._body.columnconfigure(1, weight=1)
        self._body.rowconfigure(0, weight=1)

        # ── Chat area (left) ──────────────────────────────────────────────────
        chat_col = ctk.CTkFrame(self._body, fg_color="transparent")
        chat_col.grid(row=0, column=0, sticky="nsew", padx=(16, 4), pady=12)
        chat_col.rowconfigure(0, weight=1)
        chat_col.columnconfigure(0, weight=1)

        # Title
        header = ctk.CTkFrame(chat_col, fg_color="transparent")
        header.pack(fill="x")
        styled_label(header, text="🤖 FlameAI Chat", size=18, weight="bold").pack(side="left")
        styled_label(header, text="Ask about microgravity combustion", size=12,
                     color=TEXT_MUTED).pack(side="left", padx=12)
        clear_btn = styled_button(header, text="Clear", command=self._clear_chat,
                                  width=70, height=30, accent=BG_TERTIARY)
        clear_btn.pack(side="right")

        # Scrollable messages
        self._messages_frame = ctk.CTkScrollableFrame(
            chat_col, fg_color=BG_PRIMARY,
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        self._messages_frame.pack(fill="both", expand=True, pady=(10, 8))

        # Input bar
        input_bar = ctk.CTkFrame(chat_col, fg_color=BG_SECONDARY, corner_radius=12,
                                 border_width=1, border_color=BORDER)
        input_bar.pack(fill="x", pady=(0, 4))

        self._input = ctk.CTkEntry(
            input_bar, placeholder_text="Ask FlameAI about fire safety in space…",
            fg_color=BG_TERTIARY, border_width=0,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
            corner_radius=8, font=ctk.CTkFont(size=14), height=40,
        )
        self._input.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        self._input.bind("<Return>", lambda e: self._on_send())

        self._send_btn = styled_button(input_bar, text="Send ➤", command=self._on_send,
                                       width=90, height=38)
        self._send_btn.pack(side="right", padx=(0, 10), pady=8)

        # ── Sources panel (right) ─────────────────────────────────────────────
        sources_col = ctk.CTkFrame(self._body, fg_color=BG_SECONDARY, corner_radius=12,
                                   border_width=1, border_color=BORDER, width=280)
        sources_col.grid(row=0, column=1, sticky="nsew", padx=(4, 16), pady=12)
        sources_col.pack_propagate(False)

        styled_label(sources_col, text="📚 Sources Used", size=15, weight="bold").pack(
            anchor="w", padx=14, pady=(14, 6))
        ctk.CTkFrame(sources_col, fg_color=BORDER, height=1).pack(fill="x", padx=10, pady=4)

        self._sources_list = ctk.CTkScrollableFrame(
            sources_col, fg_color="transparent",
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        self._sources_list.pack(fill="both", expand=True, padx=6, pady=6)

        self._no_sources_lbl = styled_label(
            self._sources_list,
            text="Sources will appear here\nwhen you ask questions.",
            size=12, color=TEXT_MUTED,
        )
        self._no_sources_lbl.pack(pady=30)

    # ── Welcome message ───────────────────────────────────────────────────────

    def _add_welcome(self):
        self._add_message(
            "ai",
            "👋 Hello! I am FlameAI, your microgravity combustion research assistant.\n\n"
            "I can help you with:\n"
            "• 🔬 Experiment details (SAFFIRE, BASS, ACME, SoFIE, FLEX, SPICE)\n"
            "• 🔥 Flame behavior, sphericity, and cool flames in space\n"
            "• 🛡️ Fire safety recommendations for Moon and Mars habitats\n"
            "• 📊 Research data analysis and material comparisons\n\n"
            "Ask me anything about fire safety in human space exploration!",
        )

    # ── Message rendering ─────────────────────────────────────────────────────

    def _add_message(self, role: str, text: str, sources: list | None = None):
        cleaned_text = clean_markdown_text(text)
        self._messages.append({"role": role, "text": cleaned_text})
        is_user = role == "user"
        anchor = "e" if is_user else "w"
        bg = ACCENT_ORANGE if is_user else BG_SECONDARY
        border = ACCENT_ORANGE if is_user else BORDER
        padx_l = 80 if is_user else 8
        padx_r = 8 if is_user else 80

        bubble = ctk.CTkFrame(self._messages_frame, fg_color=bg, corner_radius=14,
                              border_width=1, border_color=border)
        bubble.pack(anchor=anchor, fill="x", padx=(padx_l, padx_r), pady=6)

        sender = "You" if is_user else "🤖 FlameAI"
        styled_label(bubble, text=sender, size=11, weight="bold",
                     color=TEXT_PRIMARY if is_user else ACCENT_ORANGE).pack(
            anchor="w", padx=14, pady=(10, 2))

        msg_label = ctk.CTkLabel(
            bubble, text=cleaned_text, font=ctk.CTkFont(size=13),
            text_color=TEXT_PRIMARY, anchor="w", justify="left",
            wraplength=550,
        )
        msg_label.pack(anchor="w", padx=14, pady=(2, 10))

        # Show inline sources below AI messages
        if sources and not is_user:
            self._render_inline_sources(bubble, sources)

        # Auto-scroll
        self._messages_frame.after(50, self._messages_frame._parent_canvas.yview_moveto, 1.0)

    def _render_inline_sources(self, parent, sources):
        src_frame = ctk.CTkFrame(parent, fg_color=BG_TERTIARY, corner_radius=8)
        src_frame.pack(fill="x", padx=12, pady=(0, 10))
        styled_label(src_frame, text="📎 Sources Cited:", size=11, weight="bold",
                     color=ACCENT_BLUE).pack(anchor="w", padx=8, pady=(6, 2))
        for s in sources[:5]:
            clean_s = clean_markdown_text(str(s))
            styled_label(src_frame, text=f"  • {clean_s}", size=11,
                         color=TEXT_SECONDARY).pack(anchor="w", padx=8)
        ctk.CTkFrame(src_frame, height=4, fg_color="transparent").pack()

    # ── Sources panel update ──────────────────────────────────────────────────

    def _update_sources_panel(self, sources: list):
        if self._no_sources_lbl and self._no_sources_lbl.winfo_exists():
            self._no_sources_lbl.destroy()
            self._no_sources_lbl = None

        # Clear existing cards in panel to show current query sources
        for child in list(self._sources_list.winfo_children()):
            child.destroy()

        if not sources:
            self._no_sources_lbl = styled_label(
                self._sources_list,
                text="No background research sources required for this conversational query.",
                size=11, color=TEXT_MUTED, wraplength=220,
            )
            self._no_sources_lbl.pack(pady=20, padx=10)
            return

        for s in sources[:8]:
            card = styled_card(self._sources_list)
            card.pack(fill="x", padx=4, pady=3)
            clean_s = clean_markdown_text(str(s))
            styled_label(card, text=f"📄 {clean_s}", size=11, color=TEXT_PRIMARY, wraplength=210).pack(
                anchor="w", padx=10, pady=8)

    # ── Typing indicator ──────────────────────────────────────────────────────

    def _show_typing(self):
        self._typing_label = ctk.CTkFrame(self._messages_frame, fg_color=BG_SECONDARY,
                                          corner_radius=14, border_width=1, border_color=BORDER)
        self._typing_label.pack(anchor="w", fill="x", padx=(8, 80), pady=6)
        inner = ctk.CTkFrame(self._typing_label, fg_color="transparent")
        inner.pack(padx=14, pady=10)
        styled_label(inner, text="🤖 FlameAI is thinking", size=12,
                     color=ACCENT_ORANGE, weight="bold").pack(side="left")
        self._dots_label = styled_label(inner, text="", size=12, color=ACCENT_ORANGE)
        self._dots_label.pack(side="left", padx=4)
        self._animate_dots()

    def _animate_dots(self):
        if not self._is_thinking:
            return
        try:
            current = self._dots_label.cget("text")
            next_dots = "." if len(current) >= 3 else current + "."
            self._dots_label.configure(text=next_dots)
            self.after(400, self._animate_dots)
        except Exception:
            pass

    def _hide_typing(self):
        if self._typing_label and self._typing_label.winfo_exists():
            self._typing_label.destroy()
            self._typing_label = None

    # ── Send / receive ────────────────────────────────────────────────────────

    def _on_send(self):
        query = self._input.get().strip()
        if not query or self._is_thinking:
            return
        self._input.delete(0, "end")
        self._add_message("user", query)
        self._is_thinking = True
        self._show_typing()
        threading.Thread(target=self._run_query, args=(query,), daemon=True).start()

    def _run_query(self, query: str):
        answer = ""
        sources: list[str] = []
        try:
            if self._rag:
                result = self._rag.query(query)
                if isinstance(result, dict):
                    answer = result.get("answer", str(result))
                    sources = result.get("sources", [])
                else:
                    answer = str(result)
            else:
                # Demo mode
                time.sleep(1.0)
                answer = self._demo_response(query)
                sources = ["SAFFIRE-IV Dataset", "BASS-II Experiment Log"]
        except Exception as exc:
            answer = f"Error processing query: {exc}"

        self._is_thinking = False
        try:
            self.after(0, self._hide_typing)
            self.after(0, self._add_message, "ai", answer, sources)
            self.after(0, self._update_sources_panel, sources)
        except Exception:
            pass

    def _demo_response(self, query: str) -> str:
        q = query.lower()
        if "saffire" in q:
            return ("The SAFFIRE (Spacecraft Fire Safety) experiments are a series of "
                    "large-scale fire tests conducted aboard uncrewed Cygnus cargo vehicles. "
                    "SAFFIRE-IV demonstrated that large-scale fire growth rates in microgravity "
                    "are 2-3× slower than on Earth, but flame spread patterns are fundamentally "
                    "different due to the absence of buoyancy-driven convection.\n\n"
                    "Key parameters: O2 at 21%, pressure 14.7 psia, sample size up to 1m.")
        if "material" in q or "safe" in q:
            return ("In microgravity, material flammability can differ dramatically from "
                    "Earth conditions. Materials that are self-extinguishing in 1g may sustain "
                    "burning in microgravity due to reduced buoyant flow. NASA uses NASA-STD-6001 "
                    "Test 1 for material screening, but microgravity-specific testing (e.g., SoFIE) "
                    "provides more accurate risk assessments.\n\n"
                    "Recommended safe materials include modified Nomex blends and certain "
                    "fluoropolymer coatings.")
        return ("In microgravity combustion research, flames behave very "
                "differently than on Earth. Without buoyancy, flames become more spherical, "
                "burn cooler, and can exhibit unique cool flame regimes.\n\n"
                "Would you like to know more about a specific experiment (SAFFIRE, BASS, "
                "ACME, SoFIE, FLEX, or SPICE)?")

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _clear_chat(self):
        for w in list(self._messages_frame.winfo_children()):
            w.destroy()
        self._messages.clear()
        self._add_welcome()
