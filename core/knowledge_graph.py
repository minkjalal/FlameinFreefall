"""
NetworkX-based knowledge graph for microgravity combustion experiments.
Provides structured relationship querying to augment the RAG pipeline.
"""

import logging
from typing import Any, Optional

import networkx as nx

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """In-memory knowledge graph of experiment entities and their relationships."""

    # Canonical node types
    NODE_TYPES = {"experiment", "material", "condition", "finding", "safety_implication"}

    # Canonical edge (relationship) types
    EDGE_TYPES = {
        "tests_material",
        "uses_condition",
        "produces_finding",
        "implies_safety",
    }

    def __init__(self):
        self.graph = nx.DiGraph()
        logger.info("KnowledgeGraph initialised (empty).")

    # ── Build ─────────────────────────────────────────────────────────────────

    def build_from_data(self, experiments_data: list[dict[str, Any]]) -> None:
        """Populate the graph from a list of experiment records.

        Expected record schema (all fields optional except *name*)::

            {
                "name": str,
                "category": str,
                "materials": [str | {"name": str, ...}],
                "conditions": [str | {"name": str, ...}],
                "findings":  [str | {"description": str, ...}],
                "safety_implications": [str | {"description": str, ...}],
                ...
            }
        """
        for record in experiments_data:
            exp_name = record.get("name", record.get("experiment_name"))
            if not exp_name:
                continue

            self._add_node(exp_name, "experiment", record)

            # Materials
            for mat in _as_list(record.get("materials")):
                mat_name = _get_name(mat)
                if mat_name:
                    self._add_node(mat_name, "material", mat if isinstance(mat, dict) else {})
                    self.graph.add_edge(exp_name, mat_name, relationship="tests_material")

            # Conditions
            for cond in _as_list(record.get("conditions")):
                cond_name = _get_name(cond)
                if cond_name:
                    self._add_node(cond_name, "condition", cond if isinstance(cond, dict) else {})
                    self.graph.add_edge(exp_name, cond_name, relationship="uses_condition")

            # Findings / results
            for finding in _as_list(record.get("findings", record.get("results"))):
                finding_name = _get_description(finding)
                if finding_name:
                    short = finding_name[:120]
                    self._add_node(short, "finding", finding if isinstance(finding, dict) else {})
                    self.graph.add_edge(exp_name, short, relationship="produces_finding")

            # Safety implications
            for safety in _as_list(record.get("safety_implications", record.get("safety"))):
                safety_text = _get_description(safety)
                if safety_text:
                    short = safety_text[:120]
                    self._add_node(short, "safety_implication", safety if isinstance(safety, dict) else {})
                    self.graph.add_edge(exp_name, short, relationship="implies_safety")

                    # Link safety implications back to related materials
                    for mat in _as_list(record.get("materials")):
                        mat_name = _get_name(mat)
                        if mat_name:
                            self.graph.add_edge(mat_name, short, relationship="implies_safety")

        logger.info(
            "KnowledgeGraph built — %d nodes, %d edges",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    # ── Query ─────────────────────────────────────────────────────────────────

    def query_related(self, node_name: str, depth: int = 2) -> Optional[nx.DiGraph]:
        """Return a subgraph of nodes within *depth* hops of *node_name*.

        Uses undirected traversal (ignores edge direction) to find all
        neighbours, then returns the directed subgraph induced by those nodes.
        """
        if node_name not in self.graph:
            # Try case-insensitive fuzzy match
            node_name = self._fuzzy_find(node_name)
            if node_name is None:
                return None

        undirected = self.graph.to_undirected()
        related_nodes = set(
            nx.single_source_shortest_path_length(undirected, node_name, cutoff=depth).keys()
        )
        return self.graph.subgraph(related_nodes).copy()

    def get_experiment_connections(self, experiment_name: str) -> dict[str, list[str]]:
        """Return all directly-connected entities for an experiment, grouped by type."""
        connections: dict[str, list[str]] = {
            "materials": [],
            "conditions": [],
            "findings": [],
            "safety_implications": [],
        }

        resolved = experiment_name
        if experiment_name not in self.graph:
            resolved = self._fuzzy_find(experiment_name)
            if resolved is None:
                return connections

        for _, target, data in self.graph.edges(resolved, data=True):
            rel = data.get("relationship", "")
            node_type = self.graph.nodes[target].get("node_type", "")
            if rel == "tests_material" or node_type == "material":
                connections["materials"].append(target)
            elif rel == "uses_condition" or node_type == "condition":
                connections["conditions"].append(target)
            elif rel == "produces_finding" or node_type == "finding":
                connections["findings"].append(target)
            elif rel == "implies_safety" or node_type == "safety_implication":
                connections["safety_implications"].append(target)

        return connections

    def get_safety_implications(self, material: str) -> list[str]:
        """Return safety-implication nodes linked to a given material."""
        resolved = material
        if material not in self.graph:
            resolved = self._fuzzy_find(material)
            if resolved is None:
                return []

        implications: list[str] = []
        for _, target, data in self.graph.edges(resolved, data=True):
            if data.get("relationship") == "implies_safety":
                implications.append(target)

        # Also check inbound edges (in case an experiment links safety → material)
        for source, _, data in self.graph.in_edges(resolved, data=True):
            if self.graph.nodes[source].get("node_type") == "safety_implication":
                implications.append(source)

        return list(set(implications))

    # ── Visualisation / Export ────────────────────────────────────────────────

    def get_graph_data(self) -> dict[str, list[dict[str, Any]]]:
        """Return nodes and edges in a JSON-serialisable format."""
        nodes = [
            {"id": n, **{k: v for k, v in attrs.items()}}
            for n, attrs in self.graph.nodes(data=True)
        ]
        edges = [
            {"source": u, "target": v, **{k: val for k, val in d.items()}}
            for u, v, d in self.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def to_context_string(self, subgraph: Optional[nx.DiGraph] = None) -> str:
        """Convert a subgraph (or the full graph) into a natural-language string
        suitable for injecting into a RAG prompt."""
        g = subgraph if subgraph is not None else self.graph

        if g.number_of_nodes() == 0:
            return ""

        lines: list[str] = []

        # Group nodes by type
        by_type: dict[str, list[str]] = {}
        for node, attrs in g.nodes(data=True):
            ntype = attrs.get("node_type", "other")
            by_type.setdefault(ntype, []).append(node)

        for ntype in ["experiment", "material", "condition", "finding", "safety_implication"]:
            nodes = by_type.get(ntype, [])
            if not nodes:
                continue
            label = ntype.replace("_", " ").title() + "s"
            lines.append(f"## {label}")
            for n in nodes:
                lines.append(f"- {n}")

        lines.append("")
        lines.append("## Relationships")
        for u, v, d in g.edges(data=True):
            rel = d.get("relationship", "related_to").replace("_", " ")
            lines.append(f"- {u} → ({rel}) → {v}")

        return "\n".join(lines)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _add_node(self, name: str, node_type: str, attrs: Any = None):
        """Add or update a node with a type label and optional extra attributes."""
        extra = {}
        if isinstance(attrs, dict):
            extra = {k: v for k, v in attrs.items() if isinstance(v, (str, int, float, bool))}
        self.graph.add_node(name, node_type=node_type, **extra)

    def _fuzzy_find(self, name: str) -> Optional[str]:
        """Case-insensitive substring match against existing node names."""
        lower = name.lower()
        for node in self.graph.nodes:
            if lower == node.lower() or lower in node.lower():
                return node
        return None


# ── Module-level helpers ──────────────────────────────────────────────────────


def _as_list(value: Any) -> list:
    """Normalise a value to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _get_name(item: Any) -> Optional[str]:
    """Extract a name string from a dict-or-string item."""
    if isinstance(item, str):
        return item.strip() or None
    if isinstance(item, dict):
        return (item.get("name") or item.get("material") or item.get("label") or "").strip() or None
    return None


def _get_description(item: Any) -> Optional[str]:
    """Extract a description string from a dict-or-string item."""
    if isinstance(item, str):
        return item.strip() or None
    if isinstance(item, dict):
        return (
            item.get("description") or item.get("text") or item.get("finding") or item.get("implication") or ""
        ).strip() or None
    return None
