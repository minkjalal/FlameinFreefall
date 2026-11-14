"""
Conversation memory with JSON persistence for the Flame in Freefall application.
Stores conversation turns with timestamps and cited sources.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from config import MEMORY_FILE

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Persistent conversation history."""

    def __init__(self, memory_file: str | None = None):
        self._file = memory_file or MEMORY_FILE
        self._turns: list[dict[str, Any]] = []
        self.load()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_turn(
        self,
        user_msg: str,
        ai_response: str,
        sources: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Append a conversation turn.

        Args:
            user_msg: The user's message / question.
            ai_response: The AI-generated answer.
            sources: Optional list of source metadata dicts.
        """
        turn = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_msg,
            "ai_response": ai_response,
            "sources": sources or [],
        }
        self._turns.append(turn)
        self.save()

    def get_recent_context(self, n: int = 5) -> str:
        """Format the last *n* turns into a string suitable for prompt context."""
        recent = self._turns[-n:] if n > 0 else []
        if not recent:
            return ""

        parts: list[str] = ["## Recent Conversation"]
        for turn in recent:
            parts.append(f"User: {turn['user_message']}")
            # Truncate long AI responses to avoid blowing up the context window
            response_preview = turn["ai_response"][:500]
            if len(turn["ai_response"]) > 500:
                response_preview += "…"
            parts.append(f"Assistant: {response_preview}")
            parts.append("")  # blank line between turns

        return "\n".join(parts)

    def get_full_history(self) -> list[dict[str, Any]]:
        """Return a copy of all stored turns."""
        return list(self._turns)

    def clear(self) -> None:
        """Reset conversation memory and delete the backing file."""
        self._turns.clear()
        if os.path.exists(self._file):
            try:
                os.remove(self._file)
                logger.info("Memory file deleted: %s", self._file)
            except OSError as e:
                logger.warning("Could not delete memory file: %s", e)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Write the conversation history to disk as JSON."""
        try:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as fh:
                json.dump(self._turns, fh, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("Failed to save memory: %s", e)

    def load(self) -> None:
        """Load conversation history from disk if the file exists."""
        if not os.path.isfile(self._file):
            self._turns = []
            return

        try:
            with open(self._file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._turns = data
                logger.info("Loaded %d conversation turns from %s", len(data), self._file)
            else:
                logger.warning("Unexpected memory format — starting fresh.")
                self._turns = []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load memory (%s) — starting fresh.", e)
            self._turns = []

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._turns)

    def __bool__(self) -> bool:
        return bool(self._turns)
