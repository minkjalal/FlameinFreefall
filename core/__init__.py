"""
Core engine for the Flame in Freefall application.
"""

from core.gemini_client import GeminiClient
from core.memory import ConversationMemory
from core.knowledge_graph import KnowledgeGraph
from core.vectorstore import VectorStore
from core.rag_pipeline import RAGPipeline
from core.ingestion import load_and_chunk_data
from core.embeddings import embed_texts

__all__ = [
    "GeminiClient",
    "ConversationMemory",
    "KnowledgeGraph",
    "VectorStore",
    "RAGPipeline",
    "load_and_chunk_data",
    "embed_texts",
]
