"""
Space-themed color palette and styling utilities for Flame in Freefall.
"""
import customtkinter as ctk

# ── Color Constants ───────────────────────────────────────────────────────────
BG_PRIMARY = "#0a0e17"       # deep space dark – main background
BG_SECONDARY = "#111827"     # card / panel backgrounds
BG_TERTIARY = "#1f2937"      # hover / active / input backgrounds
ACCENT_ORANGE = "#f97316"    # fire / flame primary accent
ACCENT_BLUE = "#3b82f6"      # informational accent
ACCENT_RED = "#ef4444"       # danger / warning
ACCENT_GREEN = "#22c55e"     # success / positive
TEXT_PRIMARY = "#f9fafb"      # headings, body text
TEXT_SECONDARY = "#9ca3af"    # subtitles, descriptions
TEXT_MUTED = "#6b7280"        # placeholders, disabled text
BORDER = "#374151"            # borders and dividers

# ── Derived / convenience aliases ─────────────────────────────────────────────
SIDEBAR_BG = "#060911"
CARD_BG = BG_SECONDARY
INPUT_BG = BG_TERTIARY
HOVER_BG = "#1a2332"
ACTIVE_NAV = ACCENT_ORANGE

# ── Matplotlib dark theme parameters ─────────────────────────────────────────
MPL_DARK_PARAMS = {
    "figure.facecolor": BG_SECONDARY,
    "axes.facecolor": BG_SECONDARY,
    "axes.edgecolor": BORDER,
    "axes.labelcolor": TEXT_PRIMARY,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY,
    "text.color": TEXT_PRIMARY,
    "grid.color": BORDER,
    "grid.alpha": 0.3,
    "legend.facecolor": BG_TERTIARY,
    "legend.edgecolor": BORDER,
}


def apply_mpl_dark_theme():
    """Apply the space-dark Matplotlib rcParams globally."""
    try:
        import matplotlib as mpl
        mpl.rcParams.update(MPL_DARK_PARAMS)
    except ImportError:
        pass


def apply_space_theme():
    """Set CustomTkinter appearance and default colour theme."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def styled_card(parent, **kwargs):
    """Return a CTkFrame pre-styled as a card."""
    defaults = dict(
        fg_color=CARD_BG,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def styled_button(parent, text="", command=None, accent=ACCENT_ORANGE, **kwargs):
    """Return a CTkButton styled with the space theme."""
    defaults = dict(
        text=text,
        command=command,
        fg_color=accent,
        hover_color=_darken(accent),
        text_color=TEXT_PRIMARY,
        corner_radius=8,
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def styled_entry(parent, placeholder="", **kwargs):
    """Return a CTkEntry styled with the space theme."""
    defaults = dict(
        placeholder_text=placeholder,
        fg_color=INPUT_BG,
        border_color=BORDER,
        text_color=TEXT_PRIMARY,
        placeholder_text_color=TEXT_MUTED,
        corner_radius=8,
        font=ctk.CTkFont(size=14),
    )
    defaults.update(kwargs)
    return ctk.CTkEntry(parent, **defaults)


def styled_label(parent, text="", size=14, color=TEXT_PRIMARY, weight="normal", **kwargs):
    """Return a CTkLabel styled with the space theme."""
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=color,
        font=ctk.CTkFont(size=size, weight=weight),
        **kwargs,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _darken(hex_color: str, factor: float = 0.8) -> str:
    """Darken a hex colour by *factor* (0-1)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"
