"""
Vector store for the Flame in Freefall application.
Uses ChromaDB when installed, with seamless fallback to in-memory NumPy/Scikit-learn
cosine similarity vector store.
"""

import json
import logging
import os
from typing import Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    chromadb = None
    HAS_CHROMADB = False

import numpy as np

from config import CHROMA_DB_DIR, EMBEDDING_DIMENSION, TOP_K_RESULTS
from core.embeddings import embed_texts

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "flame_in_freefall"


class VectorStore:
    """Vector store providing semantic search over experiment data chunks."""

    def __init__(self, persist_dir: str | None = None):
        self._persist_dir = persist_dir or CHROMA_DB_DIR
        self._use_chroma = HAS_CHROMADB
        self._collection = None
        self._fallback_docs: list[dict[str, Any]] = []
        self._fallback_vectors: Optional[np.ndarray] = None

        if self._use_chroma:
            try:
                os.makedirs(self._persist_dir, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=self._persist_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name=_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(
                    "ChromaDB VectorStore initialised with %d documents",
                    self._collection.count(),
                )
            except Exception as e:
                logger.warning("ChromaDB init failed (%s), switching to in-memory store", e)
                self._use_chroma = False

        if not self._use_chroma:
            logger.info("Using NumPy vector store fallback (persistent JSON cache).")
            self._load_fallback_cache()

    # ── Fallback Cache Persistence ────────────────────────────────────────────

    def _cache_file_path(self) -> str:
        return os.path.join(self._persist_dir, "vector_cache.json")

    def _load_fallback_cache(self) -> None:
        cpath = self._cache_file_path()
        if os.path.exists(cpath):
            try:
                with open(cpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._fallback_docs = data.get("docs", [])
                vectors = data.get("vectors", [])
                if vectors:
                    self._fallback_vectors = np.array(vectors, dtype=np.float32)
                logger.info("Loaded %d documents from local vector cache.", len(self._fallback_docs))
            except Exception as e:
                logger.warning("Could not read vector cache: %s", e)

    def _save_fallback_cache(self) -> None:
        os.makedirs(self._persist_dir, exist_ok=True)
        cpath = self._cache_file_path()
        try:
            vectors_list = self._fallback_vectors.tolist() if self._fallback_vectors is not None else []
            with open(cpath, "w", encoding="utf-8") as f:
                json.dump({"docs": self._fallback_docs, "vectors": vectors_list}, f)
        except Exception as e:
            logger.warning("Could not write vector cache: %s", e)

    # ── Add Documents ─────────────────────────────────────────────────────────

    def add_documents(self, chunks: list[dict[str, Any]]) -> int:
        """Add chunked documents with embeddings and metadata."""
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)

        if self._use_chroma and self._collection is not None:
            try:
                existing_count = self._collection.count()
                ids = [f"doc_{existing_count + i}" for i in range(len(chunks))]
                metadatas = [
                    {k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                     for k, v in c.get("metadata", {}).items()}
                    for c in chunks
                ]
                self._collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                return len(chunks)
            except Exception as e:
                logger.warning("Failed to add to ChromaDB (%s), using fallback.", e)

        # Fallback NumPy addition
        new_vecs = np.array(embeddings, dtype=np.float32)
        if self._fallback_vectors is None or len(self._fallback_vectors) == 0:
            self._fallback_vectors = new_vecs
        else:
            self._fallback_vectors = np.vstack([self._fallback_vectors, new_vecs])

        self._fallback_docs.extend(chunks)
        self._save_fallback_cache()
        return len(chunks)

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict[str, Any]]:
        """Search for the most relevant documents given a query string."""
        if not query.strip():
            return []

        query_vec = embed_texts([query])[0]

        if self._use_chroma and self._collection is not None and self._collection.count() > 0:
            try:
                results = self._collection.query(
                    query_embeddings=[query_vec],
                    n_results=min(top_k, self._collection.count()),
                    include=["documents", "metadatas", "distances"],
                )
                hits: list[dict[str, Any]] = []
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                dists = results.get("distances", [[]])[0]

                for doc, meta, dist in zip(docs, metas, dists):
                    score = max(0.0, 1.0 - (dist or 0.0))
                    hits.append({"text": doc, "metadata": meta, "score": score})
                return hits
            except Exception as e:
                logger.warning("ChromaDB query failed: %s; using fallback", e)

        # NumPy cosine similarity search
        if self._fallback_vectors is None or len(self._fallback_docs) == 0:
            return []

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr = q_arr / q_norm

        # Vector norms
        norms = np.linalg.norm(self._fallback_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_vecs = self._fallback_vectors / norms

        scores = np.dot(normalized_vecs, q_arr)
        top_indices = np.argsort(scores)[::-1][:top_k]

        hits = []
        for idx in top_indices:
            doc = self._fallback_docs[idx]
            hits.append({
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "score": float(scores[idx]),
            })

        return hits

    def get_documents_by_source(self, source_name: str) -> list[dict[str, Any]]:
        """Retrieve all documents matching a specific source file, ordered by chunk_index."""
        docs: list[dict[str, Any]] = []
        if self._use_chroma and self._collection is not None:
            try:
                res = self._collection.get(where={"source": source_name})
                documents = res.get("documents", [])
                metadatas = res.get("metadatas", [])
                for d, m in zip(documents, metadatas):
                    docs.append({"text": d, "metadata": m, "score": 1.0})
            except Exception as e:
                logger.warning("ChromaDB get_documents_by_source failed: %s", e)

        if not docs and self._fallback_docs:
            for item in self._fallback_docs:
                if item.get("metadata", {}).get("source") == source_name:
                    docs.append({
                        "text": item.get("text", ""),
                        "metadata": item.get("metadata", {}),
                        "score": 1.0,
                    })

        # Sort sequentially by chunk_index
        docs.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
        return docs

    def get_collection_stats(self) -> dict[str, Any]:
        """Return basic statistics about the stored documents."""
        count = self._collection.count() if (self._use_chroma and self._collection) else len(self._fallback_docs)
        return {
            "collection_name": _COLLECTION_NAME,
            "document_count": count,
            "storage_backend": "ChromaDB" if self._use_chroma else "NumPy Local Store",
            "persist_directory": self._persist_dir,
        }
