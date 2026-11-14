"""
Main entry point for Flame in Freefall.
AI-Powered Fire Safety Insights from Microgravity Combustion Data.
NASA Space Apps Challenge 2026 — Team Eagle20 (Haldwani, India).
"""

import os
import sys
import tempfile

# Pre-configure writable directory for matplotlib cache
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_cache"))

import logging

from config import APP_TITLE
from ui.app import FlameApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("FlameInFreefall")


def main():
    logger.info("Starting %s…", APP_TITLE)
    try:
        app = FlameApp()
        app.mainloop()
    except Exception as e:
        logger.critical("Fatal application error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
