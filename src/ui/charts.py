"""
charts.py – Chart rendering helpers for Siteworks.

All charts use Plotly for interactivity.  Chart styling is consistent:
- Colour scale: green (high score) → yellow → red (low score)
- Labels are always visible for non-engineer readability.
"""

from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data.schema import CATEGORIES, ScoringResult

# City line colors (grouped bar / radar) — teal-forward, colorblind-friendly
CITY_COLORWAY = ("#0d9488", "#0284c7", "#7c3aed", "#d97706", "#db2777", "#059669", "#4f46e5")

_CHART_FONT = dict(family="'DM Sans', 'Segoe UI', sans-serif", size=13, color="#1e293b")
_CHART_PAPER = "rgba(0,0,0,0)"
_CHART_PLOT = "#f1f5f9"

# Consistent colour scale for scores
_COLOR_SCALE = [
    [0.0, "#d73027"],   # 1 – red
    [0.25, "#fc8d59"],
    [0.5, "#fee08b"],   # 3 – yellow
    [0.75, "#91cf60"],
    [1.0, "#1a9850"],   # 5 – green
]

_CAT_SHORT: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "Hydro",
    "Climate & Operational Physics":  "Climate",
    "Economic & Social Impact":       "Economic",
    "Natural Hazards":                "Hazards",
    "Biodiversity":                   "Biodiversity",
}


def _base_layout(**kwargs) -> dict:
    """Shared Plotly layout fragments."""
    base = dict(
        font=_CHART_FONT,
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_PLOT,
        hoverlabel=dict(
            bgcolor="#ffffff",
            font_size=13,
            font_family="'DM Sans', sans-serif",
            bordercolor="#e2e8f0",
        ),
    )
    base.update(kwargs)
    return base


def _score_colour(score: float, min_s: float = 1.0, max_s: float = 5.0) -> str:
    """Map a score to a hex colour along the green-yellow-red scale."""
    norm = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
    for threshold, colour in reversed(_COLOR_SCALE):
        if norm >= threshold:
            return colour
    return _COLOR_SCALE[0][1]


# ---------------------------------------------------------------------------
# Bar chart: total scores
# ---------------------------------------------------------------------------

def total_score_bar(results: List[ScoringResult]) -> go.Figure:
    """Horizontal bar chart of total weighted scores for all cities."""
    cities = [r.city for r in results]
    scores = [r.total_score for r in results]
    colours = [_score_colour(s) for s in scores]
    ranks = [r.rank for r in results]

    fig = go.Figure(
        go.Bar(
            y=cities,
            x=scores,
            orientation="h",
            marker_color=colours,
            text=[f"#{rank}  {score:.2f}" for rank, score in zip(ranks, scores)],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text="Overall site suitability", font=dict(size=16)),
            xaxis=dict(
                range=[0, 5.5],
                title="Weighted score (1–5)",
                gridcolor="#e2e8f0",
                zeroline=False,
            ),
            yaxis=dict(categoryorder="total ascending", title=""),
            height=340,
            margin=dict(l=8, r=72, t=56, b=36),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# Grouped bar chart: category scores
# ---------------------------------------------------------------------------

def category_score_grouped_bar(results: List[ScoringResult]) -> go.Figure:
    """Grouped bar chart – one group per category, bars coloured by score."""
    rows = []
    for r in results:
        for cat in CATEGORIES:
            rows.append({
                "City": r.city,
                "Category": _CAT_SHORT.get(cat, cat),
                "Score": r.category_scores.get(cat, 0.0),
            })
    df = pd.DataFrame(rows)

    fig = px.bar(
        df,
        x="Category",
        y="Score",
        color="City",
        barmode="group",
        color_discrete_sequence=list(CITY_COLORWAY),
        text_auto=".2f",
    )
    fig.for_each_trace(
        lambda tr: tr.update(marker_line_width=0, marker_line_color="white")
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text="Scores by sustainability category", font=dict(size=16)),
            yaxis=dict(
                range=[0, 5.5],
                title="Category average (1–5)",
                gridcolor="#e2e8f0",
                zeroline=False,
            ),
            xaxis=dict(title="", tickangle=-18),
            height=420,
            margin=dict(l=8, r=8, t=56, b=96),
            legend_title_text="City",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.28,
                xanchor="center",
                x=0.5,
            ),
        )
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    return fig


# ---------------------------------------------------------------------------
# Radar chart: category scores per city
# ---------------------------------------------------------------------------

def radar_chart(results: List[ScoringResult], highlight: Optional[str] = None) -> go.Figure:
    """Radar / spider chart of category scores per city."""
    cats_short = [_CAT_SHORT.get(c, c) for c in CATEGORIES]
    cats_closed = cats_short + [cats_short[0]]  # close the polygon

    fig = go.Figure()
    colours = list(CITY_COLORWAY)

    for idx, r in enumerate(results):
        values = [r.category_scores.get(c, 0.0) for c in CATEGORIES]
        values_closed = values + [values[0]]
        opacity = 1.0 if (highlight is None or r.city == highlight) else 0.25

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=cats_closed,
                fill="toself",
                name=r.city,
                line_color=colours[idx % len(colours)],
                opacity=opacity,
            )
        )

    fig.update_layout(
        **_base_layout(
            polar=dict(
                bgcolor=_CHART_PLOT,
                radialaxis=dict(
                    range=[0, 5],
                    tickvals=[1, 2, 3, 4, 5],
                    gridcolor="#e2e8f0",
                    linecolor="#cbd5e1",
                ),
                angularaxis=dict(linecolor="#cbd5e1", gridcolor="#e2e8f0"),
            ),
            title=dict(text="Category profile (radar)", font=dict(size=16)),
            height=420,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.12,
                xanchor="center",
                x=0.5,
            ),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# Side-by-side comparison chart
# ---------------------------------------------------------------------------

def comparison_bar(a: ScoringResult, b: ScoringResult) -> go.Figure:
    """Horizontal grouped bar chart comparing two cities across categories."""
    cats_short = [_CAT_SHORT.get(c, c) for c in CATEGORIES]
    a_scores = [a.category_scores.get(c, 0.0) for c in CATEGORIES]
    b_scores = [b.category_scores.get(c, 0.0) for c in CATEGORIES]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=a.city,
            y=cats_short,
            x=a_scores,
            orientation="h",
            marker_color=CITY_COLORWAY[0],
            marker_line_width=0,
            text=[f"{s:.2f}" for s in a_scores],
            textposition="outside",
        )
    )
    fig.add_trace(
        go.Bar(
            name=b.city,
            y=cats_short,
            x=b_scores,
            orientation="h",
            marker_color=CITY_COLORWAY[2],
            marker_line_width=0,
            text=[f"{s:.2f}" for s in b_scores],
            textposition="outside",
        )
    )
    fig.update_layout(
        **_base_layout(
            barmode="group",
            title=dict(
                text=f"{a.city} vs {b.city} — categories",
                font=dict(size=16),
            ),
            xaxis=dict(
                range=[0, 5.8],
                title="Score (1–5)",
                gridcolor="#e2e8f0",
                zeroline=False,
            ),
            yaxis=dict(title=""),
            height=380,
            margin=dict(l=8, r=72, t=56, b=36),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# Score delta chart (for comparison view)
# ---------------------------------------------------------------------------

def delta_bar(a: ScoringResult, b: ScoringResult) -> go.Figure:
    """Bar chart showing A − B score delta per category."""
    cats_short = [_CAT_SHORT.get(c, c) for c in CATEGORIES]
    deltas = [
        a.category_scores.get(c, 0.0) - b.category_scores.get(c, 0.0)
        for c in CATEGORIES
    ]
    colours = ["#1a9850" if d >= 0 else "#d73027" for d in deltas]

    fig = go.Figure(
        go.Bar(
            y=cats_short,
            x=deltas,
            orientation="h",
            marker_color=colours,
            text=[f"{d:+.2f}" for d in deltas],
            textposition="outside",
            hovertemplate="%{y}: %{x:+.2f}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        **_base_layout(
            title=dict(
                text=f"Gap: {a.city} − {b.city} (by category)",
                font=dict(size=16),
            ),
            xaxis=dict(
                title="Score difference",
                range=[-3, 3],
                gridcolor="#e2e8f0",
                zeroline=True,
                zerolinecolor="#94a3b8",
            ),
            yaxis=dict(title=""),
            height=320,
            margin=dict(l=8, r=72, t=56, b=36),
        )
    )
    return fig
