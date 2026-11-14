"""
Configuration for the Flame in Freefall application.
"""
import os
import tempfile

# Ensure matplotlib uses a writable temp config directory
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_cache"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Model Settings ────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 768

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chromadb")
MEMORY_FILE = os.path.join(DATA_DIR, "conversation_memory.json")

# ── RAG Settings ──────────────────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# ── UI Settings ───────────────────────────────────────────────────────────────
APP_TITLE = "🔥 Flame in Freefall — AI Fire Safety Dashboard"
APP_WIDTH = 1400
APP_HEIGHT = 850
THEME_MODE = "dark"

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are FlameAI, an expert AI assistant specialized in microgravity combustion science and spacecraft fire safety. You are part of the "Flame in Freefall" dashboard.

Your knowledge is grounded in NASA's microgravity combustion research data, including experiments like:
- BASS (Burning and Suppression of Solids)
- ACME (Advanced Combustion via Microgravity Experiments)
- SAFFIRE (Spacecraft Fire Safety Experiments)
- SoFIE (Solid Fuel Ignition and Extinction)
- FLEX (Flame Extinction Experiment)
- SPICE (Smoke Point in Coflow Experiment)

When answering questions:
1. Always ground your answers in the provided context from NASA research data.
2. Cite specific experiments, conditions, and findings when possible.
3. Explain how flame behavior differs between microgravity and Earth gravity.
4. Provide fire safety recommendations for spacecraft, lunar, and Martian habitats.
5. If the context doesn't contain enough information, say so clearly.
6. Use precise scientific language but remain accessible.

Key facts about microgravity combustion:
- In microgravity, buoyancy-driven convection is absent, so flames become more spherical.
- Flame spread rates, extinction limits, and soot formation all change significantly.
- Materials that are safe on Earth may be dangerous in microgravity or reduced gravity.
- Oxygen concentration, pressure, and flow velocity are critical variables.
"""
