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
        title="Overall Site Suitability Score (1–5)",
        xaxis=dict(range=[0, 5.5], title="Weighted Score"),
        yaxis=dict(categoryorder="total ascending"),
        height=320,
        margin=dict(l=10, r=60, t=50, b=30),
        plot_bgcolor="white",
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
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Category Scores by City",
        text_auto=".2f",
    )
    fig.update_layout(
        yaxis=dict(range=[0, 5.5], title="Score"),
        height=380,
        margin=dict(l=10, r=10, t=50, b=80),
        legend_title_text="City",
        plot_bgcolor="white",
    )
    fig.update_traces(textposition="outside")
    return fig


# ---------------------------------------------------------------------------
# Radar chart: category scores per city
# ---------------------------------------------------------------------------

def radar_chart(results: List[ScoringResult], highlight: Optional[str] = None) -> go.Figure:
    """Radar / spider chart of category scores per city."""
    cats_short = [_CAT_SHORT.get(c, c) for c in CATEGORIES]
    cats_closed = cats_short + [cats_short[0]]  # close the polygon

    fig = go.Figure()
    colours = px.colors.qualitative.Set2

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
        polar=dict(
            radialaxis=dict(range=[0, 5], tickvals=[1, 2, 3, 4, 5]),
        ),
        title="Category Score Radar",
        height=400,
        showlegend=True,
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
            marker_color="#4C72B0",
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
            marker_color="#DD8452",
            text=[f"{s:.2f}" for s in b_scores],
            textposition="outside",
        )
    )
    fig.update_layout(
        barmode="group",
        title=f"Category Comparison: {a.city} vs {b.city}",
        xaxis=dict(range=[0, 5.8], title="Score"),
        yaxis=dict(title=""),
        height=360,
        margin=dict(l=10, r=70, t=50, b=30),
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
        title=f"Score Difference: {a.city} (blue) minus {b.city} (orange)",
        xaxis=dict(title="Δ Score", range=[-3, 3]),
        yaxis=dict(title=""),
        height=300,
        margin=dict(l=10, r=70, t=50, b=30),
        plot_bgcolor="white",
    )
    return fig
