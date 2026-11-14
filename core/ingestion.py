"""
Data ingestion and chunking module for the Flame in Freefall application.
Loads experiment, material, finding, and guideline data from JSON files
and splits them into overlapping text chunks with rich metadata for retrieval.
"""

import json
import logging
import os
from typing import Any

from config import CHUNK_OVERLAP, CHUNK_SIZE, KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)


def load_and_chunk_data(
    knowledge_dir: str | None = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Load all JSON files from the knowledge base directory, then chunk them.

    Handles root arrays or dicts containing 'experiments', 'materials',
    'findings', or 'guidelines' arrays.
    """
    knowledge_dir = knowledge_dir or KNOWLEDGE_BASE_DIR

    if not os.path.isdir(knowledge_dir):
        logger.warning("Knowledge base directory does not exist: %s", knowledge_dir)
        return []

    all_chunks: list[dict[str, Any]] = []

    for filename in sorted(os.listdir(knowledge_dir)):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(knowledge_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load %s: %s", filepath, e)
            continue

        records = _extract_records(data)

        for record in records:
            chunks = _chunk_record(record, filename, chunk_size, chunk_overlap)
            all_chunks.extend(chunks)

    logger.info("Ingested %d total chunks from %s", len(all_chunks), knowledge_dir)
    return all_chunks


def _extract_records(data: Any) -> list[dict]:
    """Extract individual item records from various JSON structures."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    elif isinstance(data, dict):
        for key in ["experiments", "materials", "findings", "guidelines", "items"]:
            if key in data and isinstance(data[key], list):
                return [r for r in data[key] if isinstance(r, dict)]
        return [data]
    return []


def _chunk_record(
    record: dict, source_file: str, chunk_size: int, chunk_overlap: int
) -> list[dict[str, Any]]:
    """Convert a single entity record into overlapping text chunks."""
    name = (
        record.get("name")
        or record.get("title")
        or record.get("acronym")
        or record.get("id")
        or "unknown"
    )
    category = record.get("category", record.get("environment", "General"))
    full_text = _extract_text(record)

    if not full_text.strip():
        return []

    text_chunks = _split_text(full_text, chunk_size, chunk_overlap)

    return [
        {
            "text": chunk,
            "metadata": {
                "experiment_name": str(name),
                "source": source_file,
                "category": str(category),
                "chunk_index": idx,
                "total_chunks": len(text_chunks),
            },
        }
        for idx, chunk in enumerate(text_chunks)
    ]


def _extract_text(record: dict) -> str:
    """Flatten a dictionary into a semantically rich text string for search."""
    parts: list[str] = []

    name = record.get("name") or record.get("title")
    if name:
        parts.append(f"Entity: {name}")

    simple_keys = [
        "acronym", "category", "platform", "years", "environment",
        "description", "overview", "summary", "objective", "objectives",
        "common_uses", "microgravity_behavior", "earth_vs_micro",
        "safety_recommendation", "recommendation", "rationale",
        "implications_for_spacecraft", "quantitative_result",
    ]
    for key in simple_keys:
        val = record.get(key)
        if val:
            if isinstance(val, list):
                parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(v) for v in val)}")
            else:
                parts.append(f"{key.replace('_', ' ').title()}: {val}")

    structured_keys = [
        "parameters", "flame_characteristics", "key_findings",
        "safety_implications", "conditions", "materials_tested",
    ]
    for key in structured_keys:
        val = record.get(key)
        if not val:
            continue
        if isinstance(val, list):
            items = [_flatten_item(item) for item in val]
            parts.append(f"{key.replace('_', ' ').title()}:\n" + "\n".join(f"- {i}" for i in items))
        elif isinstance(val, dict):
            parts.append(f"{key.replace('_', ' ').title()}: {_flatten_item(val)}")
        else:
            parts.append(f"{key.replace('_', ' ').title()}: {val}")

    # Extract any remaining custom keys (e.g. guidelines, full_text, requirements)
    handled_keys = set(["name", "title", "id"] + simple_keys + structured_keys)
    for key, val in record.items():
        if key in handled_keys or not val:
            continue
        if isinstance(val, list):
            items = [_flatten_item(item) for item in val]
            parts.append(f"{key.replace('_', ' ').title()}:\n" + "\n".join(f"- {i}" for i in items))
        elif isinstance(val, dict):
            parts.append(f"{key.replace('_', ' ').title()}: {_flatten_item(val)}")
        else:
            parts.append(f"{key.replace('_', ' ').title()}: {val}")

    return "\n\n".join(parts)


def _flatten_item(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return "; ".join(f"{k}: {v}" for k, v in item.items())
    return str(item)


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            snap_zone = text[end - chunk_size // 5 : end]
            for sep in [". ", ".\n", "\n\n", "\n"]:
                pos = snap_zone.rfind(sep)
                if pos != -1:
                    end = (end - chunk_size // 5) + pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = max(start + 1, end - chunk_overlap)

    return chunks
