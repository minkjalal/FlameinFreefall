"""
Embedding utilities for the Flame in Freefall application.
Primary: Google Gemini text-embedding-004 model.
Fallback: Deterministic TF-IDF / hashing vectors when API is unavailable.
"""

import hashlib
import logging
import math
import re
import time
from collections import Counter
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

from config import EMBEDDING_DIMENSION, EMBEDDING_MODEL, GEMINI_API_KEY

logger = logging.getLogger(__name__)

_BATCH_SIZE = 50
_REQUESTS_PER_MINUTE = 60
_MIN_INTERVAL = 60.0 / _REQUESTS_PER_MINUTE


def embed_texts(
    texts: list[str],
    api_key: Optional[str] = None,
    dimension: int = EMBEDDING_DIMENSION,
) -> list[list[float]]:
    """Embed a list of texts, falling back to TF-IDF vectors on API failure or offline mode."""
    if not texts:
        return []

    key = api_key or GEMINI_API_KEY
    if key and key != "your_gemini_api_key_here" and HAS_GENAI:
        try:
            return _embed_with_gemini(texts, key)
        except Exception as e:
            logger.warning("Gemini embedding failed, falling back to TF-IDF: %s", e)

    return _embed_tfidf_fallback(texts, dimension)


def _embed_with_gemini(texts: list[str], api_key: str) -> list[list[float]]:
    """Call the Gemini embedding API with batching and rate limiting."""
    genai.configure(api_key=api_key)

    all_embeddings: list[list[float]] = []
    last_request_time = 0.0

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]

        elapsed = time.time() - last_request_time
        if elapsed < _MIN_INTERVAL and last_request_time > 0:
            time.sleep(_MIN_INTERVAL - elapsed)

        result = genai.embed_content(
            model=f"models/{EMBEDDING_MODEL}",
            content=batch,
            task_type="retrieval_document",
        )
        last_request_time = time.time()

        embeddings = result.get("embedding", [])
        if embeddings and isinstance(embeddings[0], float):
            all_embeddings.append(embeddings)
        else:
            all_embeddings.extend(embeddings)

    return all_embeddings


def _embed_tfidf_fallback(texts: list[str], dimension: int) -> list[list[float]]:
    """Generate dense, L2-normalized pseudo-embeddings via word hashing."""
    tokenized = [_tokenize(t) for t in texts]

    # Document frequency
    doc_freq: Counter = Counter()
    for tokens in tokenized:
        doc_freq.update(set(tokens))

    num_docs = max(len(texts), 1)
    vectors: list[list[float]] = []

    for tokens in tokenized:
        vec = [0.0] * dimension
        tf = Counter(tokens)

        for token, count in tf.items():
            df = doc_freq.get(token, 1)
            idf = math.log((1 + num_docs) / (1 + df)) + 1.0
            weight = count * idf
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dimension
            vec[idx] += weight

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0

        vectors.append(vec)

    return vectors


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text."""
    words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    stop_words = {
        "the", "and", "in", "of", "to", "a", "is", "for", "on", "that", "by", "this",
        "with", "i", "you", "it", "not", "or", "be", "are", "from", "at", "as", "your",
        "all", "have", "new", "more", "an", "was", "we", "will", "can", "us", "if",
    }
    return [w for w in words if w not in stop_words]
