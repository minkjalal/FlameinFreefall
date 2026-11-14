"""
General utility and helper functions for Flame in Freefall.
"""

from datetime import datetime
from typing import Any


def format_timestamp(dt: datetime | None = None) -> str:
    """Format current or given datetime into a clean string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_len: int = 100, suffix: str = "…") -> str:
    """Truncate text to max_len characters with an ellipsis."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def color_for_risk(score: float | int | str) -> str:
    """Return a hex color based on risk score (0-100 or level string).

    For score (0-100 where 100 is safest):
    - 75-100: Green (Low risk)
    - 50-74: Blue/Yellow (Moderate risk)
    - 30-49: Orange (High risk)
    - 0-29: Red (Critical risk)
    """
    if isinstance(score, str):
        level = score.upper()
        if "LOW" in level:
            return "#22c55e"
        elif "MOD" in level:
            return "#eab308"
        elif "HIGH" in level:
            return "#f97316"
        elif "CRIT" in level:
            return "#ef4444"
        try:
            score = float(score)
        except ValueError:
            return "#9ca3af"

    try:
        val = float(score)
        if val >= 75:
            return "#22c55e"  # Green
        elif val >= 55:
            return "#eab308"  # Yellow
        elif val >= 35:
            return "#f97316"  # Orange
        else:
            return "#ef4444"  # Red
    except Exception:
        return "#9ca3af"


def format_percentage(value: float | int | None) -> str:
    """Format a float or int as percentage string."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def clean_markdown_text(text: str) -> str:
    """Clean markdown artifacts (**, *, ##, //, backticks) for display in Tkinter UI."""
    if not text:
        return ""

    import re

    lines = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()

        # Remove header markers (###, ##, #)
        line = re.sub(r"^#{1,6}\s+", "", line)

        # Remove bullet artifacts like '• ##' or '• ###'
        line = re.sub(r"^[•\-\*]\s*#{1,6}\s*", "• ", line)

        # Remove comments like '// ...'
        if line.startswith("//"):
            continue

        # Remove bold **text** -> text
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)

        # Remove italics *text* or _text_ -> text
        line = re.sub(r"(?<!\*)\*([^\*\s][^\*]*?)\*(?!\*)", r"\1", line)
        line = re.sub(r"(?<!_)_([^_\s][^_]*?)_(?!_)", r"\1", line)

        # Remove backticks `code` -> code
        line = re.sub(r"`([^`]+)`", r"\1", line)

        # Clean footer note about API key to a subtle clean notice
        if "Running with local RAG knowledge grounding" in line:
            line = "[Mode: Local NASA Combustion Knowledge Base]"

        lines.append(line)

    cleaned = "\n".join(lines)
    # Collapse 3+ newlines into 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def safe_get(d: dict, key: str, default: Any = None) -> Any:
    """Safely get a key from a dictionary, handling None dictionary."""
    if not isinstance(d, dict):
        return default
    return d.get(key, default)
