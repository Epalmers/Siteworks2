"""
tables.py – Ranked table rendering helpers for Siteworks.
"""

from typing import Dict, List

import pandas as pd
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

from src.data.schema import CATEGORIES, ScoringResult

_CAT_SHORT: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "Hydro",
    "Climate & Operational Physics":  "Climate",
    "Economic & Social Impact":       "Economic",
    "Natural Hazards":                "Hazards",
    "Biodiversity":                   "Biodiversity",
}

# Rankings table only: original red–amber–green heatmap (charts use Okabe–Ito in ``palette``).
_TABLE_CMAP = LinearSegmentedColormap.from_list(
    "siteworks_rankings_table",
    ["#be6863", "#d8b08d", "#e4dcbe", "#a8c3a4", "#688f76"],
)


def render_ranking_table(results: List[ScoringResult]) -> None:
    """Render the ranked city table with colour-coded scores."""
    rows = []
    for r in results:
        row: Dict = {
            "Rank": f"#{r.rank}",
            "City": r.city,
            "Total Score": round(r.total_score, 2),
        }
        for cat in CATEGORIES:
            row[_CAT_SHORT.get(cat, cat)] = round(r.category_scores.get(cat, 0.0), 2)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Colour gradient on numeric columns
    score_cols = ["Total Score"] + [_CAT_SHORT.get(c, c) for c in CATEGORIES]

    styled = (
        df.style
        .background_gradient(
            subset=score_cols,
            cmap=_TABLE_CMAP,
            vmin=1.0,
            vmax=5.0,
        )
        .format({col: "{:.2f}" for col in score_cols})
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#f2f6fb"),
                        ("color", "#0f172a"),
                        ("font-weight", "700"),
                        ("font-size", "0.9rem"),
                        ("border-bottom", "1px solid #c8d5e5"),
                        ("text-align", "left"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("border-bottom", "1px solid #e7edf5"),
                    ],
                },
            ]
        )
        .set_properties(
            subset=score_cols,
            **{"text-align": "right", "color": "#0f172a", "font-weight": "700"},
        )
        .set_properties(
            subset=["Rank", "City"],
            **{"text-align": "left", "color": "#0f172a", "font-weight": "600"},
        )
        .set_properties(
            subset=["Rank"],
            **{"background-color": "#edf3fb", "font-weight": "700"},
        )
        .set_properties(
            subset=["Total Score"],
            **{"font-size": "1.02rem", "font-weight": "800"},
        )
    )

    st.dataframe(styled, width="stretch", hide_index=True, row_height=42)


def render_subcategory_table(
    city_name: str,
    city_data,
    scoring_module,
) -> None:
    """
    Show a breakdown of subcategory scores for one city.

    Parameters:
        city_name   : Name of the city.
        city_data   : CityData object for the city.
        scoring_module : the scoring module (passed to avoid circular import).
    """
    from src.data.schema import SUBCATEGORIES, SUBCATEGORY_TOOLTIPS, SUBCATEGORY_SOURCES

    rows = []
    for cat in CATEGORIES:
        subs = SUBCATEGORIES.get(cat, [])
        avg, missing = scoring_module.compute_category_score(city_data, cat)
        for sub in subs:
            entry = city_data.subcategory_scores.get(sub)
            score = entry.score if entry else None
            raw = entry.raw_value if entry else "—"
            rows.append({
                "Category": cat,
                "Subcategory": sub,
                "Score": round(score, 2) if score is not None else "—",
                "Raw Value": raw or "—",
                "Description": SUBCATEGORY_TOOLTIPS.get(sub, ""),
                "Source": SUBCATEGORY_SOURCES.get(sub, ""),
            })

    df = pd.DataFrame(rows)

    # Style only numeric score rows
    numeric_mask = pd.to_numeric(df["Score"], errors="coerce").notna()
    df_display = df.copy()

    st.dataframe(
        df_display[["Category", "Subcategory", "Score", "Raw Value", "Description"]],
        width="stretch",
        hide_index=True,
        row_height=36,
    )
