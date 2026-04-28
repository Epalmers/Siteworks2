"""
compare.py – Two-city comparison view for Siteworks.
"""

from typing import Dict, List

import streamlit as st

from src.data.schema import CATEGORIES, SUBCATEGORIES, CityData, ScoringResult
from src.logic.summaries import city_comparison_summary
from src.ui.charts import comparison_bar

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
    if len(all_results) < 2:
        st.warning("Add at least two cities in the workbook to compare.")
        return

    # Dropdowns use rank order; defaults are #1 vs #2 until rankings change (sidebar rerun).
    city_names = [r.city for r in all_results]
    rank_fp = tuple((r.city, r.rank) for r in all_results)
    _fp_key = "_compare_ranking_fingerprint"
    if (
        _fp_key not in st.session_state
        or st.session_state[_fp_key] != rank_fp
    ):
        st.session_state[_fp_key] = rank_fp
        st.session_state["compare_a"] = all_results[0].city
        st.session_state["compare_b"] = all_results[1].city

    # Each list omits the other dropdown's pick so cities never duplicate as options.
    other_b = st.session_state["compare_b"]
    other_a = st.session_state["compare_a"]
    options_first = [c for c in city_names if c != other_b]
    options_second = [c for c in city_names if c != other_a]

    col1, col2 = st.columns(2)
    with col1:
        city_a = st.selectbox(
            "First city",
            options=options_first,
            key="compare_a",
        )
    with col2:
        city_b = st.selectbox(
            "Second city",
            options=options_second,
            key="compare_b",
        )

    if city_a == city_b:
        st.warning("Choose two different cities to compare.")
        return

    # Retrieve results
    result_map: Dict[str, ScoringResult] = {r.city: r for r in all_results}
    ra = result_map[city_a]
    rb = result_map[city_b]

    st.info(city_comparison_summary(ra, rb))

    st.markdown("##### Composite score")
    m1, m2 = st.columns(2)
    with m1:
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

    st.plotly_chart(comparison_bar(ra, rb), width="stretch")

    st.markdown("##### Relative strengths")
    s1, s2 = st.columns(2)

    with s1:
        _render_strengths_weaknesses(ra, rb, city_a)

    with s2:
        _render_strengths_weaknesses(rb, ra, city_b)

    # Subcategory detail
    with st.expander("All subcategories (table)", expanded=False):
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

    st.caption("Advantages vs opponent")
    adv = [(c, d) for c, d in sorted_cats if d > 0]
    if adv:
        for cat, diff in adv[:3]:
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;&nbsp;+{diff:.2f} · {_CAT_SHORT.get(cat, cat)}"
            )
    else:
        st.caption("No categories where this city leads.")

    st.caption("Trailing categories")
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
    st.dataframe(df, width="stretch", hide_index=True)
