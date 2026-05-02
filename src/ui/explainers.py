"""
explainers.py – Tooltips, plain-language panels, and data transparency views.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import streamlit as st

from src.data.schema import (
    CATEGORIES,
    SUBCATEGORIES,
    SUBCATEGORY_TOOLTIPS,
    SUBCATEGORY_SOURCES,
    DEFAULT_WEIGHTS,
    ScoringResult,
)
from src.logic.summaries import (
    top_city_summary,
    second_ranked_city_summary,
    scenario_summary,
)


def _markdown_subcategory_sources(
    sub: str,
    workbook_sources: Optional[Dict[str, List[Tuple[str, str]]]],
) -> str:
    """Build source link markdown: one link if all cities agree; otherwise per-city lines."""
    fallback = SUBCATEGORY_SOURCES.get(sub, "").strip()

    def _link(url: str) -> str:
        return f"[source]({url})"

    if not workbook_sources:
        return f" · {_link(fallback)}" if fallback else ""

    pairs = workbook_sources.get(sub)
    if not pairs:
        return f" · {_link(fallback)}" if fallback else ""

    url_to_cities: Dict[str, List[str]] = defaultdict(list)
    for city, url in pairs:
        if not url:
            continue
        u = str(url).strip()
        if not u.startswith("http"):
            continue
        url_to_cities[u].append(city)

    if not url_to_cities:
        return f" · {_link(fallback)}" if fallback else ""

    if len(url_to_cities) == 1:
        only = next(iter(url_to_cities.keys()))
        return f" · {_link(only)}"

    parts = []
    for url in sorted(url_to_cities.keys()):
        cities = sorted(dict.fromkeys(url_to_cities[url]))
        label = ", ".join(cities)
        parts.append(f"{label}: {_link(url)}")
    return " · " + " · ".join(parts)


def _plain_text(md_text: str) -> str:
    """Remove lightweight markdown markers for HTML-rendered strings."""
    return (
        md_text.replace("**", "")
        .replace("__", "")
        .replace("`", "")
    )


def render_summary_panel(
    results: List[ScoringResult],
    scenario_name: str,
) -> None:
    """Plain-language summary of current rankings."""
    if not results:
        st.warning("No results to summarise.")
        return

    top = results[0]

    with st.container(border=True):
        st.markdown("##### Interpretation & Insights")
        st.caption("Read this section as an executive summary of the current weighting scenario.")
        if len(results) == 1:
            key_takeaway = (
                f"Only one city is available: {top.city} with a total score of "
                f"{top.total_score:.2f}. Add more cities to enable leader vs trailer comparisons."
            )
            st.markdown(f'<p class="sw-insight-key">{key_takeaway}</p>', unsafe_allow_html=True)
            st.markdown(
                (
                    '<div class="sw-insight-card">'
                    '<p class="sw-insight-title">Current Candidate</p>'
                    f'<p class="sw-insight-body">{_plain_text(top_city_summary(top))}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2, gap="small")
            c1.metric("City", top.city, f"{top.total_score:.2f}")
            c2.metric("Comparison status", "Insufficient data", "need at least 2 cities")
            st.info("Comparative scenario interpretation is available when at least two cities are ranked.")
            return

        second = results[1]
        spread = top.total_score - second.total_score

        key_takeaway = (
            f"{top.city} currently leads with a total score of {top.total_score:.2f}, "
            f"ahead of runner-up {second.city} by {spread:.2f} points under this weighting profile."
        )
        st.markdown(f'<p class="sw-insight-key">{key_takeaway}</p>', unsafe_allow_html=True)
        a, b = st.columns(2, gap="medium")
        with a:
            st.markdown(
                (
                    '<div class="sw-insight-card">'
                    '<p class="sw-insight-title">Leading Candidate</p>'
                    f'<p class="sw-insight-body">{_plain_text(top_city_summary(top))}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        with b:
            st.markdown(
                (
                    '<div class="sw-insight-card">'
                    '<p class="sw-insight-title">Second-ranked Candidate</p>'
                    f'<p class="sw-insight-body">{_plain_text(second_ranked_city_summary(second))}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        c1, c2, c3 = st.columns(3, gap="small")
        c1.metric("Leader", top.city, f"{top.total_score:.2f}")
        c2.metric("Runner-up", second.city, f"{second.total_score:.2f}")
        c3.metric("Spread", f"{spread:.2f}", "leader vs runner-up")
        st.info(scenario_summary(scenario_name, results))


def render_scoring_explainer_body() -> None:
    """Scoring methodology (no expander wrapper)."""
    st.markdown(
        """
**Weighted multi-criteria decision analysis (MCDA)** — each city is scored on **16**
subcategories in **5** themes. All scores use a **1–5** scale (**5** = best for
data-center siting).

**1 · Subcategory scores**  
Higher is always better for siting.

**2 · Category score**  
Subcategories within each theme are averaged.

**3 · Weighted total**
```
Total = (Hydro × w₁) + (Climate × w₂) + (Economic × w₃) + (Hazards × w₄) + (Bio × w₅)
```
Weights are normalized to sum to **1.0** (sidebar sliders).

**4 · Rank**  
Cities sort from highest total to lowest.

---
*Decision-support only — validate with site work, legal review, and engineering.*
"""
    )


def render_scoring_explainer() -> None:
    """Explain the scoring methodology in plain language."""
    with st.expander("How scoring works", expanded=False):
        render_scoring_explainer_body()


def render_category_explainer_body(
    workbook_sources: Optional[Dict[str, List[Tuple[str, str]]]] = None,
) -> None:
    """Category reference (no expander wrapper)."""
    for cat in CATEGORIES:
        st.markdown(f"**{cat}** · default weight **{DEFAULT_WEIGHTS[cat]:.0%}**")
        for sub in SUBCATEGORIES.get(cat, []):
            tooltip = SUBCATEGORY_TOOLTIPS.get(sub, "")
            src_frag = _markdown_subcategory_sources(sub, workbook_sources)
            st.caption(f"• **{sub}** — {tooltip}{src_frag}")
        st.markdown("")


def render_category_explainer(
    workbook_sources: Optional[Dict[str, List[Tuple[str, str]]]] = None,
) -> None:
    """Show each category with its subcategories and tooltips."""
    with st.expander("Category definitions", expanded=False):
        render_category_explainer_body(workbook_sources)


def render_data_quality_panel(
    quality_notes: List[str],
    from_workbook: bool,
) -> None:
    """Show data source and quality notes."""
    with st.expander("Data quality & assumptions", expanded=False):
        if from_workbook:
            st.success("Loaded from **Data_Center_Site_Selector_RH.xlsx**.")
        else:
            st.warning(
                "The app requires **Data_Center_Site_Selector_RH.xlsx** in `data/`. "
                "Place the file and use **Refresh data** in the sidebar."
            )

        st.markdown("**Notes & caveats**")
        for note in quality_notes:
            st.markdown(f"- {note}")

        st.caption(
            "Data loads only from **Data_Center_Site_Selector_RH.xlsx** in `data/`. "
            "Use **Refresh data** in the sidebar after changing the file."
        )

