"""
Data loader utilities for loading and querying knowledge base files.
"""

import json
import logging
import os
from typing import Any, Optional

from config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)


def _load_json_file(filename: str) -> Any:
    """Helper to load a JSON file from the knowledge base directory."""
    path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    if not os.path.isfile(path):
        logger.warning("File not found: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error reading %s: %s", path, e)
        return None


def load_experiments() -> list[dict[str, Any]]:
    """Load all experiment records from experiments.json."""
    data = _load_json_file("experiments.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("experiments", [])
    return []


def load_materials() -> list[dict[str, Any]]:
    """Load all material records from materials.json."""
    data = _load_json_file("materials.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("materials", [])
    return []


def load_findings() -> list[dict[str, Any]]:
    """Load all research findings from findings.json."""
    data = _load_json_file("findings.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("findings", [])
    return []


def load_safety_guidelines() -> list[dict[str, Any]]:
    """Load all safety guidelines from safety_guidelines.json."""
    data = _load_json_file("safety_guidelines.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("guidelines", [])
    return []


def load_all_data() -> dict[str, list[dict[str, Any]]]:
    """Load all knowledge base data into a consolidated dictionary."""
    return {
        "experiments": load_experiments(),
        "materials": load_materials(),
        "findings": load_findings(),
        "guidelines": load_safety_guidelines(),
    }


def get_experiment_by_id(exp_id: str) -> Optional[dict[str, Any]]:
    """Find an experiment by id, acronym, or name (case-insensitive)."""
    target = exp_id.strip().lower()
    for exp in load_experiments():
        if (
            exp.get("id", "").lower() == target
            or exp.get("acronym", "").lower() == target
            or exp.get("name", "").lower() == target
        ):
            return exp
    return None


def get_material_by_name(name: str) -> Optional[dict[str, Any]]:
    """Find a material by name (case-insensitive substring match)."""
    target = name.strip().lower()
    for mat in load_materials():
        mat_name = mat.get("name", "").lower()
        if target in mat_name or mat_name in target:
            return mat
    return None
