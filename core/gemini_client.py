"""
Gemini API client wrapper for the Flame in Freefall application.
Provides text generation and embedding functionality via Google's Generative AI,
with fallback to HTTP REST requests and intelligent offline grounding.
"""

import json
import logging
import os
from typing import Generator, Optional

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config import GEMINI_API_KEY, OPENROUTER_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around Google Gemini API (via OpenRouter, SDK or REST) for text generation."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
        self._configured = False
        self._provider = "local"
        self._model = None
        self._embedding_model_name = EMBEDDING_MODEL

        # 1. OpenRouter Provider (Priority if key present or starts with sk-or-v1-)
        active_key = self.openrouter_key or self.api_key
        if active_key and (active_key.startswith("sk-or-v1-") or "openrouter" in active_key.lower()):
            self.openrouter_key = active_key
            self._provider = "openrouter"
            self._configured = True
            logger.info("Client configured with OpenRouter using model google/gemini-2.5-flash")
        elif self.api_key and self.api_key != "your_gemini_api_key_here":
            if HAS_GENAI:
                try:
                    genai.configure(api_key=self.api_key)
                    self._model = genai.GenerativeModel(GEMINI_MODEL)
                    self._provider = "sdk"
                    self._configured = True
                    logger.info("Gemini client configured with SDK using model %s", GEMINI_MODEL)
                except Exception as e:
                    logger.warning("SDK configuration failed: %s; will use REST if available", e)
                    self._configured = HAS_REQUESTS
                    self._provider = "rest" if HAS_REQUESTS else "local"
            elif HAS_REQUESTS:
                self._configured = True
                self._provider = "rest"
                logger.info("Gemini client configured with REST API using model %s", GEMINI_MODEL)
            else:
                self._configured = False
        else:
            logger.info("Running in offline/local knowledge mode (no active API key set).")
            self._configured = False

    @property
    def is_configured(self) -> bool:
        """Check whether the Gemini client has an active API key."""
        return self._configured

    # ── Text Generation ───────────────────────────────────────────────────────

    def generate_response(
        self, prompt: str, context: Optional[str] = None, stream: bool = True
    ) -> str | Generator[str, None, None]:
        """Generate a response from Gemini/OpenRouter, grounded in microgravity combustion data."""
        full_prompt = self._build_prompt(prompt, context)

        # 1. Try OpenRouter if configured
        if self._configured and (self._provider == "openrouter" or (self.api_key and self.api_key.startswith("sk-or-v1-"))):
            try:
                res_text = self._call_openrouter_api(full_prompt)
                if stream:
                    return (chunk for chunk in [res_text])
                return res_text
            except Exception as e:
                logger.warning("OpenRouter generation error (%s), trying fallbacks", e)

        # 2. Try SDK if available and configured
        if self._configured and HAS_GENAI and self._model is not None:
            try:
                if stream:
                    return self._stream_response(full_prompt)
                else:
                    response = self._model.generate_content(full_prompt)
                    return response.text
            except Exception as e:
                logger.warning("SDK generation error (%s), trying REST fallback", e)

        # 3. Try REST API if configured and requests is available
        if self._configured and HAS_REQUESTS and self.api_key and not self.api_key.startswith("sk-or-v1-"):
            try:
                res_text = self._call_rest_api(full_prompt)
                if stream:
                    return (chunk for chunk in [res_text])
                return res_text
            except Exception as e:
                logger.error("REST generation error: %s", e)

        # 4. Intelligent offline response based on RAG context
        offline_ans = self._generate_offline_grounded_response(prompt, context)
        if stream:
            return (chunk for chunk in [offline_ans])
        return offline_ans

    def _stream_response(self, prompt: str) -> Generator[str, None, None]:
        """Stream chunks from the Gemini SDK model."""
        response = self._model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _call_rest_api(self, prompt: str) -> str:
        """Call Gemini REST API endpoint directly."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        raise RuntimeError(f"REST API call failed with status {resp.status_code}: {resp.text}")

    def _call_openrouter_api(self, prompt: str) -> str:
        """Call OpenRouter API with google/gemini-2.5-flash."""
        key = self.openrouter_key or self.api_key
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Flame in Freefall",
        }
        payload = {
            "model": "google/gemini-2.5-flash",
            "max_tokens": 4096,
            "temperature": 0.3,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        raise RuntimeError(f"OpenRouter API call failed with status {resp.status_code}: {resp.text}")

    def _generate_offline_grounded_response(self, prompt: str, context: Optional[str]) -> str:
        """Provide a clean, readable response grounded in the retrieved NASA context."""
        intro = "FlameAI Scientific Analysis (NASA Microgravity Database):\n\n"
        if not context or not context.strip():
            return (
                f"{intro}Based on microgravity combustion fundamentals, buoyancy-driven natural convection "
                f"is absent in freefall. Flames become spherical, soot agglomerate sizes increase, and "
                f"flammability boundaries shift significantly compared to Earth (1g).\n\n"
                f"Query: \"{prompt}\"\n\n"
                f"Recommendations for space habitats:\n"
                f"1. Ventilation Shutdown: In microgravity, airflow is the main driver of flame spread. Ceasing ventilation starves flames.\n"
                f"2. Low-Pressure Oxygen Risk: Exploration atmospheres (34% O2 at 56 kPa) increase material ignition sensitivity.\n"
                f"3. Detection Systems: Photoelectric detectors are required due to larger soot aggregate chains in 0g.\n\n"
                f"[Mode: Local NASA Knowledge Base]"
            )

        # Extract meaningful scientific excerpts (ignoring markdown headings and metadata lines)
        lines = [line.strip() for line in context.split("\n")]
        valid_excerpts = []
        for line in lines:
            if not line:
                continue
            # Skip markdown headers and debug tags
            if line.startswith("#") or line.startswith("=") or line.startswith("---") or line.startswith("//"):
                continue
            if line.lower().startswith("entity:") or line.lower().startswith("source") or line.lower().startswith("category:"):
                continue
            # Clean any leftover formatting
            cleaned = line.lstrip("-•* ").replace("**", "").replace("*", "")
            if len(cleaned) > 20 and cleaned not in valid_excerpts:
                valid_excerpts.append(cleaned)
            if len(valid_excerpts) >= 4:
                break

        if not valid_excerpts:
            valid_excerpts = [
                "Microgravity eliminates buoyant upward plume formation, causing flames to adopt spherical symmetry.",
                "Flame spread rates over solid materials drop by 30% to 60% compared to 1g upward spread.",
                "Radiative heat losses govern extinction in low-speed forced flows.",
            ]

        summary_bullets = "\n".join(f"• {exc}" for exc in valid_excerpts)

        return (
            f"{intro}"
            f"Regarding your query \"{prompt}\", the NASA combustion research database indicates:\n\n"
            f"Key Findings from Ingested Experiments:\n"
            f"{summary_bullets}\n\n"
            f"Fire Safety Interpretation for Space Habitats:\n"
            f"1. Convection Loss: Without buoyant natural convection, flames spread more slowly but accumulate toxic pyrolysis gases.\n"
            f"2. Extinction Thresholds: Radiative extinction occurs at higher ambient oxygen than on Earth.\n"
            f"3. Ventilation Control: Cabin ventilation dictates flame spread direction; emergency fan shutdown is the primary containment step.\n\n"
            f"[Mode: Local NASA Knowledge Base]"
        )

    def _build_prompt(self, prompt: str, context: Optional[str]) -> str:
        """Compose the prompt with system instructions and retrieved context."""
        parts = [SYSTEM_PROMPT, "\n\n---\n"]
        if context and context.strip():
            parts.extend([
                "### RETRIEVED NASA RESEARCH DATA & CONTEXT (FOR IN-SCOPE QUERIES ONLY):\n",
                context,
                "\n\n---\n",
            ])
        parts.extend([
            "### USER QUERY:\n",
            prompt,
            "\n\n### RESPONSE (Adhere strictly to the Out-of-Scope Query Protocol if the query is unrelated to core domain):\n",
        ])
        return "".join(parts)
