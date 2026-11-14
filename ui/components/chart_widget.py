"""
Matplotlib chart widget embedded in a CustomTkinter frame.
"""
from __future__ import annotations

import math
import customtkinter as ctk

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend – we embed manually
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from ui.themes.space_theme import (
    BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    MPL_DARK_PARAMS,
)

# Default colour cycle for charts
CHART_COLORS = [
    ACCENT_ORANGE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
    "#a855f7", "#eab308", "#14b8a6", "#ec4899",
]


class ChartWidget(ctk.CTkFrame):
    """Embeddable chart widget supporting bar, line, radar, and pie charts."""

    def __init__(self, parent, figsize=(5, 3.5), **kwargs):
        defaults = dict(fg_color=BG_SECONDARY, corner_radius=12,
                        border_width=1, border_color=BORDER)
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        self._figsize = figsize
        self._fig_canvas = None
        self._fig = None
        self._ax = None

        if not HAS_MPL:
            lbl = ctk.CTkLabel(self, text="📊 matplotlib not installed",
                               text_color=TEXT_SECONDARY)
            lbl.pack(expand=True)
            return

        self._init_figure()
        self.bind("<Configure>", self._on_resize)

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_figure(self):
        self._fig = Figure(figsize=self._figsize, dpi=100)
        self._fig.patch.set_facecolor(BG_SECONDARY)
        self._ax = self._fig.add_subplot(111)
        self._apply_ax_style(self._ax)

        self._fig_canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._fig_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _apply_ax_style(self, ax):
        ax.set_facecolor(BG_SECONDARY)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.title.set_color(TEXT_PRIMARY)
        ax.xaxis.label.set_color(TEXT_SECONDARY)
        ax.yaxis.label.set_color(TEXT_SECONDARY)

    # ── Public chart methods ──────────────────────────────────────────────────

    def plot_bar(self, data: dict, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Bar chart.  *data*: ``{label: value, …}``"""
        if not HAS_MPL:
            return
        self._clear()
        labels = list(data.keys())
        values = list(data.values())
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
        bars = self._ax.bar(labels, values, color=colors, edgecolor="none", width=0.6)
        for bar, val in zip(bars, values):
            self._ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                          str(val), ha="center", va="bottom",
                          fontsize=9, color=TEXT_PRIMARY)
        self._ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
        self._ax.set_xlabel(xlabel)
        self._ax.set_ylabel(ylabel)
        self._ax.tick_params(axis="x", rotation=30)
        self._fig.tight_layout()
        self._fig_canvas.draw()

    def plot_line(self, data: dict, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Line chart.  *data*: ``{series_name: ([x], [y]), …}``"""
        if not HAS_MPL:
            return
        self._clear()
        for idx, (name, (xs, ys)) in enumerate(data.items()):
            color = CHART_COLORS[idx % len(CHART_COLORS)]
            self._ax.plot(xs, ys, marker="o", label=name, color=color,
                          linewidth=2, markersize=5)
        self._ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
        self._ax.set_xlabel(xlabel)
        self._ax.set_ylabel(ylabel)
        if len(data) > 1:
            self._ax.legend(fontsize=9, facecolor=BG_SECONDARY, edgecolor=BORDER,
                            labelcolor=TEXT_PRIMARY)
        self._fig.tight_layout()
        self._fig_canvas.draw()

    def plot_pie(self, data: dict, title: str = ""):
        """Pie / donut chart.  *data*: ``{label: value, …}``"""
        if not HAS_MPL:
            return
        self._clear()
        labels = list(data.keys())
        values = list(data.values())
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
        wedges, texts, autotexts = self._ax.pie(
            values, labels=labels, autopct="%1.0f%%", startangle=140,
            colors=colors, pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor=BG_SECONDARY),
            textprops=dict(color=TEXT_PRIMARY, fontsize=9),
        )
        for t in autotexts:
            t.set_color(TEXT_PRIMARY)
            t.set_fontsize(8)
        self._ax.set_title(title, fontsize=13, fontweight="bold", pad=10,
                           color=TEXT_PRIMARY)
        self._fig.tight_layout()
        self._fig_canvas.draw()

    def plot_radar(self, data: dict, title: str = ""):
        """Radar / spider chart.
        *data*: ``{series_name: {axis_label: value, …}, …}``
        All series must share the same axis labels.
        """
        if not HAS_MPL:
            return
        self._fig.clf()

        series_names = list(data.keys())
        first_series = data[series_names[0]]
        categories = list(first_series.keys())
        N = len(categories)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]  # close polygon

        ax = self._fig.add_subplot(111, polar=True)
        ax.set_facecolor(BG_SECONDARY)
        ax.spines["polar"].set_color(BORDER)
        ax.tick_params(colors=TEXT_SECONDARY)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9, color=TEXT_PRIMARY)
        ax.yaxis.grid(True, color=BORDER, alpha=0.3)
        ax.xaxis.grid(True, color=BORDER, alpha=0.3)

        for idx, (name, vals) in enumerate(data.items()):
            values = [vals[c] for c in categories] + [vals[categories[0]]]
            color = CHART_COLORS[idx % len(CHART_COLORS)]
            ax.plot(angles, values, linewidth=2, label=name, color=color)
            ax.fill(angles, values, alpha=0.15, color=color)

        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9,
                  facecolor=BG_SECONDARY, edgecolor=BORDER, labelcolor=TEXT_PRIMARY)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=20, color=TEXT_PRIMARY)
        self._fig.tight_layout()
        self._fig_canvas.draw()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clear(self):
        if self._ax is not None:
            self._ax.clear()
            self._apply_ax_style(self._ax)

    def _on_resize(self, event=None):
        if self._fig_canvas is not None:
            self._fig_canvas.draw_idle()
