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

# Fixed city color system used across charts/UI.
CITY_COLORS: Dict[str, str] = {
    "Denver": "#4f8f74",
    "Oklahoma City": "#587db7",
    "Boston": "#7f6aa8",
    "Gainesville": "#b28f73",
    "Houston": "#b86b7e",
}


def city_color(city: str) -> str:
    """Return the canonical color for a city."""
    return CITY_COLORS.get(city, "#334155")

_CHART_FONT = dict(family="'DM Sans', 'Segoe UI', sans-serif", size=13, color="#1e293b")
_CHART_PAPER = "rgba(0,0,0,0)"
_CHART_PLOT = "#f1f5f9"

# Consistent colour scale for scores
_COLOR_SCALE = [
    [0.0, "#bf6864"],
    [0.25, "#d8af8c"],
    [0.5, "#e4dab8"],
    [0.75, "#a5c3a3"],
    [1.0, "#648f75"],
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
        margin=dict(l=8, r=16, t=56, b=36),
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
    colours = [city_color(c) for c in cities]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    fig = go.Figure(
        go.Bar(
            y=cities,
            x=scores,
            orientation="h",
            marker_color=colours,
            marker_line_color="#dce6f2",
            marker_line_width=0.6,
            text=[f"{score:.2f}" for score in scores],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_vline(
        x=avg_score,
        line_dash="dot",
        line_color="#51667f",
        line_width=1.5,
        annotation_text=f"Average {avg_score:.2f}",
        annotation_position="top right",
        annotation_font_color="#1e293b",
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text="Overall Score", font=dict(size=16)),
            xaxis=dict(
                range=[0, 5.5],
                title="Weighted score (1–5)",
                gridcolor="#d8e1ec",
                zeroline=False,
                tickfont=dict(size=12.5),
            ),
            yaxis=dict(title="", autorange="reversed", tickfont=dict(size=13.5)),
            height=430,
            bargap=0.08,
            margin=dict(l=8, r=56, t=56, b=36),
        )
    )
    fig.update_traces(marker_line_width=0, cliponaxis=False)
    return fig


# ---------------------------------------------------------------------------
# Grouped bar chart: category scores
# ---------------------------------------------------------------------------

def category_score_grouped_bar(
    results: List[ScoringResult],
    emphasis_cities: Optional[List[str]] = None,
) -> go.Figure:
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

    city_order = [r.city for r in results]
    fig = px.bar(
        df,
        x="Category",
        y="Score",
        color="City",
        barmode="group",
        color_discrete_map={**CITY_COLORS},
        category_orders={"City": city_order},
        text_auto=".2f",
    )
    fig.for_each_trace(
        lambda tr: tr.update(marker_line_width=0, marker_line_color="white")
    )
    emphasis_set = set(emphasis_cities or [])
    if emphasis_set:
        fig.for_each_trace(
            lambda tr: tr.update(opacity=1.0 if tr.name in emphasis_set else 0.35)
        )
    fig.update_layout(
        **_base_layout(
            title=dict(text="Category Comparison", font=dict(size=16)),
            yaxis=dict(
                range=[0, 5.5],
                title="Category average (1–5)",
                gridcolor="#d2dbe8",
                zeroline=False,
                tickfont=dict(size=12.5),
            ),
            xaxis=dict(title="", tickangle=-6, tickfont=dict(size=13)),
            height=440,
            margin=dict(l=8, r=12, t=76, b=90),
            bargap=0.35,
            bargroupgap=0.12,
            legend_title_text="City",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
            ),
        )
    )
    fig.update_traces(textposition="outside", textfont_size=10.5, cliponaxis=False)
    return fig


# ---------------------------------------------------------------------------
# Radar chart: category scores per city
# ---------------------------------------------------------------------------

def radar_chart(results: List[ScoringResult], highlight: Optional[str] = None) -> go.Figure:
    """Radar / spider chart of category scores per city."""
    if not results:
        return go.Figure()
    cats_short = [_CAT_SHORT.get(c, c) for c in CATEGORIES]
    cats_closed = cats_short + [cats_short[0]]  # close the polygon

    fig = go.Figure()
    for _, r in enumerate(results):
        values = [r.category_scores.get(c, 0.0) for c in CATEGORIES]
        values_closed = values + [values[0]]
        is_focus = highlight is None or r.city == highlight
        opacity = 0.48 if is_focus else 0.14

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=cats_closed,
                fill="toself",
                name=r.city,
                line_color=city_color(r.city),
                line=dict(width=2.8 if is_focus else 2.0),
                fillcolor=city_color(r.city),
                opacity=opacity,
                hovertemplate="<b>%{fullData.name}</b><br>%{theta}: %{r:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        **_base_layout(
            polar=dict(
                bgcolor=_CHART_PLOT,
                radialaxis=dict(
                    range=[0, 5],
                    tickvals=[1, 2, 3, 4, 5],
                    tickfont=dict(size=11.5, color="#334155"),
                    gridcolor="#dbe3ee",
                    linecolor="#c6d3e2",
                ),
                angularaxis=dict(
                    linecolor="#c6d3e2",
                    gridcolor="#dbe3ee",
                    tickfont=dict(size=12.5, color="#334155"),
                ),
            ),
            title=dict(text="Category Profile (Radar)", font=dict(size=16)),
            height=460,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=1.0,
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
            marker_color=city_color(a.city),
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
            marker_color=city_color(b.city),
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
