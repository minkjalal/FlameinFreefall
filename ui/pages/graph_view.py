"""
Knowledge-graph visualisation page for Flame in Freefall.
"""
from __future__ import annotations

import customtkinter as ctk

from ui.themes.space_theme import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BORDER,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    styled_card, styled_label, styled_button,
)
from ui.components.search_bar import SearchBar

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

# ── Sample graph data ─────────────────────────────────────────────────────────
SAMPLE_NODES = [
    ("SAFFIRE-IV", "experiment"), ("BASS-II", "experiment"),
    ("SoFIE-GEL", "experiment"), ("FLEX-2", "experiment"),
    ("ACME-03", "experiment"), ("SPICE", "experiment"),
    ("Cotton-Fibreglass", "material"), ("PMMA", "material"),
    ("Silicone", "material"), ("Heptane", "material"),
    ("Cotton-Nomex", "material"), ("Ethylene", "material"),
    ("Slow fire growth in µg", "finding"),
    ("O₂-dependent spread", "finding"),
    ("Cool-flame regime", "finding"),
    ("Gel suppression 40% faster", "finding"),
    ("Increased soot at low flow", "finding"),
    ("Material flammability change", "safety"),
    ("Ventilation risk", "safety"),
    ("O₂ enrichment hazard", "safety"),
]

SAMPLE_EDGES = [
    ("SAFFIRE-IV", "Cotton-Fibreglass"), ("SAFFIRE-IV", "Slow fire growth in µg"),
    ("SAFFIRE-IV", "Material flammability change"),
    ("BASS-II", "PMMA"), ("BASS-II", "O₂-dependent spread"),
    ("BASS-II", "O₂ enrichment hazard"),
    ("SoFIE-GEL", "Silicone"), ("SoFIE-GEL", "Gel suppression 40% faster"),
    ("FLEX-2", "Heptane"), ("FLEX-2", "Cool-flame regime"),
    ("ACME-03", "Cotton-Nomex"), ("ACME-03", "Material flammability change"),
    ("SPICE", "Ethylene"), ("SPICE", "Increased soot at low flow"),
    ("SPICE", "Ventilation risk"),
    ("Cotton-Fibreglass", "Material flammability change"),
    ("PMMA", "O₂ enrichment hazard"),
    ("Heptane", "Cool-flame regime"),
]

NODE_COLORS = {
    "experiment": ACCENT_ORANGE,
    "material": ACCENT_BLUE,
    "finding": ACCENT_GREEN,
    "safety": ACCENT_RED,
}


class GraphViewPage(ctk.CTkFrame):
    """Interactive knowledge-graph viewer powered by NetworkX + Matplotlib."""

    def __init__(self, parent, knowledge_graph=None, **kwargs):
        super().__init__(parent, fg_color=BG_PRIMARY, **kwargs)
        self._kg = knowledge_graph
        self._graph = None
        self._highlight: str | None = None
        self._build_ui()
        self._load_graph()

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(14, 6))
        styled_label(top, text="🕸️ Knowledge Graph", size=20, weight="bold").pack(side="left")
        search = SearchBar(top, placeholder="Highlight node…", on_search=self._on_search)
        search.pack(side="right", fill="x", expand=True, padx=(20, 0))

        # ── Body = graph + sidebar ────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=0, pady=0)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Canvas area
        self._canvas_frame = ctk.CTkFrame(body, fg_color=BG_SECONDARY, corner_radius=12,
                                          border_width=1, border_color=BORDER)
        self._canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 6), pady=10)

        if not HAS_NX:
            styled_label(self._canvas_frame,
                         text="📦 networkx / matplotlib not installed.\n"
                              "Install them to see the knowledge graph.",
                         size=14, color=TEXT_MUTED).pack(expand=True)

        # ── Detail sidebar ────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(body, fg_color=BG_SECONDARY, corner_radius=12,
                               border_width=1, border_color=BORDER, width=260)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(6, 20), pady=10)
        sidebar.pack_propagate(False)

        styled_label(sidebar, text="📋 Node Details", size=15, weight="bold").pack(
            anchor="w", padx=14, pady=(14, 6))
        ctk.CTkFrame(sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=10, pady=4)

        self._detail_content = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent",
            scrollbar_button_color=BG_TERTIARY,
            scrollbar_button_hover_color=ACCENT_ORANGE,
        )
        self._detail_content.pack(fill="both", expand=True, padx=6, pady=6)

        self._detail_placeholder = styled_label(
            self._detail_content,
            text="Click a node in the graph\nto see its details.",
            size=12, color=TEXT_MUTED,
        )
        self._detail_placeholder.pack(pady=30)

        # Legend
        legend_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        legend_frame.pack(fill="x", padx=14, pady=(6, 14))
        styled_label(legend_frame, text="Legend", size=12, weight="bold").pack(anchor="w", pady=(0, 4))
        for ntype, color in NODE_COLORS.items():
            row = ctk.CTkFrame(legend_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            dot = ctk.CTkFrame(row, fg_color=color, width=12, height=12, corner_radius=6)
            dot.pack(side="left", padx=(0, 6))
            styled_label(row, text=ntype.capitalize(), size=11, color=TEXT_SECONDARY).pack(side="left")

    # ── Graph ─────────────────────────────────────────────────────────────────

    def _load_graph(self):
        if not HAS_NX:
            return

        # Try core engine, fall back to sample
        nodes, edges = SAMPLE_NODES, SAMPLE_EDGES
        if self._kg:
            try:
                gdata = self._kg.get_graph_data()
                if isinstance(gdata, dict):
                    nodes = gdata.get("nodes", nodes)
                    edges = gdata.get("edges", edges)
            except Exception:
                pass

        G = nx.Graph()
        node_types = {}

        if nodes and isinstance(nodes[0], dict):
            for n in nodes:
                nid = n.get("id") or n.get("name")
                ntype = n.get("node_type") or n.get("type", "experiment")
                if nid:
                    G.add_node(nid)
                    node_types[nid] = ntype
            for e in edges:
                if isinstance(e, dict):
                    src = e.get("source")
                    tgt = e.get("target")
                    if src and tgt:
                        G.add_edge(src, tgt)
                elif isinstance(e, (list, tuple)) and len(e) >= 2:
                    G.add_edge(e[0], e[1])
        else:
            for item in nodes:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    G.add_node(item[0])
                    node_types[item[0]] = item[1]
                else:
                    G.add_node(str(item))
                    node_types[str(item)] = "experiment"
            for e in edges:
                if isinstance(e, (list, tuple)) and len(e) >= 2:
                    G.add_edge(e[0], e[1])

        self._graph = G
        self._node_types = node_types
        self._draw_graph()

    def _draw_graph(self):
        if not HAS_NX or self._graph is None:
            return

        for w in list(self._canvas_frame.winfo_children()):
            w.destroy()

        fig = Figure(figsize=(7, 5), dpi=100)
        fig.patch.set_facecolor(BG_SECONDARY)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_SECONDARY)
        ax.set_axis_off()

        pos = nx.spring_layout(self._graph, seed=42, k=1.8)

        # Node colours & sizes
        colors = []
        sizes = []
        for node in self._graph.nodes():
            ntype = self._node_types.get(node, "experiment")
            c = NODE_COLORS.get(ntype, TEXT_MUTED)
            if self._highlight and self._highlight.lower() in node.lower():
                sizes.append(900)
            else:
                sizes.append(500)
            colors.append(c)

        nx.draw_networkx_edges(self._graph, pos, ax=ax, edge_color=BORDER,
                               alpha=0.4, width=1.2)
        nx.draw_networkx_nodes(self._graph, pos, ax=ax, node_color=colors,
                               node_size=sizes, edgecolors=BORDER, linewidths=0.8)
        nx.draw_networkx_labels(self._graph, pos, ax=ax, font_size=7,
                                font_color=TEXT_PRIMARY, font_weight="bold")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self._canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

        # Click event
        def on_click(event):
            if event.xdata is None or event.ydata is None:
                return
            # Find closest node
            min_dist = float("inf")
            closest = None
            for node, (x, y) in pos.items():
                dist = (x - event.xdata) ** 2 + (y - event.ydata) ** 2
                if dist < min_dist:
                    min_dist = dist
                    closest = node
            if closest and min_dist < 0.02:
                self.after(0, self._show_node_details, closest)

        fig.canvas.mpl_connect("button_press_event", on_click)

    # ── Node details ──────────────────────────────────────────────────────────

    def _show_node_details(self, node: str):
        for w in list(self._detail_content.winfo_children()):
            w.destroy()

        ntype = self._node_types.get(node, "unknown")
        color = NODE_COLORS.get(ntype, TEXT_MUTED)

        styled_label(self._detail_content, text=node, size=16, weight="bold",
                     color=color).pack(anchor="w", pady=(4, 2))
        styled_label(self._detail_content, text=f"Type: {ntype.capitalize()}", size=12,
                     color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 8))

        # Connected nodes
        neighbors = list(self._graph.neighbors(node)) if self._graph else []
        styled_label(self._detail_content, text=f"Connections ({len(neighbors)}):",
                     size=13, weight="bold", color=TEXT_PRIMARY).pack(anchor="w", pady=(4, 4))
        for n in neighbors:
            nc = NODE_COLORS.get(self._node_types.get(n, ""), TEXT_MUTED)
            styled_label(self._detail_content, text=f"  → {n}", size=11,
                         color=nc).pack(anchor="w", pady=1)

        # Try core engine for extra info
        if self._kg:
            try:
                info = self._kg.query_related(node, depth=1)
                if info:
                    ctk.CTkFrame(self._detail_content, fg_color=BORDER, height=1).pack(
                        fill="x", pady=8)
                    styled_label(self._detail_content, text="Related Info:", size=12,
                                 weight="bold").pack(anchor="w")
                    styled_label(self._detail_content, text=str(info)[:300], size=11,
                                 color=TEXT_SECONDARY, wraplength=220).pack(anchor="w")
            except Exception:
                pass

    # ── Search / highlight ────────────────────────────────────────────────────

    def _on_search(self, query: str):
        self._highlight = query
        self._draw_graph()
