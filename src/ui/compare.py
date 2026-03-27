"""
compare.py – Two-city comparison view for Siteworks.
"""

from typing import Dict, List

import streamlit as st

from src.data.schema import CATEGORIES, SUBCATEGORIES, CityData, ScoringResult
from src.logic.summaries import city_comparison_summary
from src.ui.charts import comparison_bar, delta_bar

_CAT_SHORT: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "💧 Hydro & Regulatory",
    "Climate & Operational Physics":  "🌡️ Climate & Grid",
    "Economic & Social Impact":       "💰 Economic & Social",
    "Natural Hazards":                "⚡ Natural Hazards",
    "Biodiversity":                   "🌿 Biodiversity",
}


def render_comparison_view(
    city_data: Dict[str, CityData],
    all_results: List[ScoringResult],
) -> None:
    """Render the full two-city comparison view."""
    city_names = list(city_data.keys())

    col1, col2 = st.columns(2)
    with col1:
        city_a = st.selectbox(
            "City A", options=city_names, index=0, key="compare_a"
        )
    with col2:
        default_b = city_names[1] if len(city_names) > 1 else city_names[0]
        city_b = st.selectbox(
            "City B",
            options=city_names,
            index=city_names.index(default_b),
            key="compare_b",
        )

    if city_a == city_b:
        st.warning("Please select two different cities to compare.")
        return

    # Retrieve results
    result_map: Dict[str, ScoringResult] = {r.city: r for r in all_results}
    ra = result_map[city_a]
    rb = result_map[city_b]

    # Summary text
    st.markdown("#### 📝 Summary")
    st.info(city_comparison_summary(ra, rb))

    # Metric cards
    st.markdown("#### 🏆 Overall Score")
    m1, m2 = st.columns(2)
    with m1:
        delta_a = ra.total_score - rb.total_score
        st.metric(
            label=city_a,
            value=f"{ra.total_score:.2f}",
            delta=f"Rank #{ra.rank}",
        )
    with m2:
        st.metric(
            label=city_b,
            value=f"{rb.total_score:.2f}",
            delta=f"Rank #{rb.rank}",
        )

    # Charts
    st.plotly_chart(comparison_bar(ra, rb), use_container_width=True)
    st.plotly_chart(delta_bar(ra, rb), use_container_width=True)

    # Strengths and weaknesses
    st.markdown("#### 💪 Strengths & Weaknesses")
    s1, s2 = st.columns(2)

    with s1:
        _render_strengths_weaknesses(ra, rb, city_a)

    with s2:
        _render_strengths_weaknesses(rb, ra, city_b)

    # Subcategory detail
    with st.expander("🔍 Detailed Subcategory Comparison", expanded=False):
        _render_subcategory_comparison(
            city_a, city_b, city_data[city_a], city_data[city_b]
        )


def _render_strengths_weaknesses(
    main: ScoringResult,
    other: ScoringResult,
    label: str,
) -> None:
    """Show top strengths and weaknesses vs the other city."""
    diffs = {
        cat: main.category_scores.get(cat, 0.0) - other.category_scores.get(cat, 0.0)
        for cat in CATEGORIES
    }
    sorted_cats = sorted(diffs.items(), key=lambda x: x[1], reverse=True)

    st.markdown(f"**{label}**")

    st.markdown("✅ *Advantages over opponent:*")
    adv = [(c, d) for c, d in sorted_cats if d > 0]
    if adv:
        for cat, diff in adv[:3]:
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;&nbsp;+{diff:.2f} · {_CAT_SHORT.get(cat, cat)}"
            )
    else:
        st.caption("No categories where this city leads.")

    st.markdown("❌ *Disadvantages:*")
    disadv = [(c, d) for c, d in sorted_cats if d < 0]
    if disadv:
        for cat, diff in reversed(disadv[-3:]):
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;&nbsp;{diff:.2f} · {_CAT_SHORT.get(cat, cat)}"
            )
    else:
        st.caption("No categories where this city trails.")


def _render_subcategory_comparison(
    name_a: str,
    name_b: str,
    cd_a: CityData,
    cd_b: CityData,
) -> None:
    """Detailed subcategory table for both cities side by side."""
    import pandas as pd

    rows = []
    for cat in CATEGORIES:
        for sub in SUBCATEGORIES.get(cat, []):
            entry_a = cd_a.subcategory_scores.get(sub)
            entry_b = cd_b.subcategory_scores.get(sub)
            score_a = round(entry_a.score, 2) if entry_a else "—"
            score_b = round(entry_b.score, 2) if entry_b else "—"
            try:
                diff = round(float(score_a) - float(score_b), 2)
                diff_str = f"{diff:+.2f}"
            except (TypeError, ValueError):
                diff_str = "—"
            rows.append({
                "Category": cat,
                "Subcategory": sub,
                name_a: score_a,
                name_b: score_b,
                "Δ (A−B)": diff_str,
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
