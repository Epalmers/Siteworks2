"""
explainers.py – Tooltips, plain-language panels, and data transparency views.
"""

from typing import List

import streamlit as st

from src.data.schema import (
    CATEGORIES,
    SUBCATEGORIES,
    SUBCATEGORY_TOOLTIPS,
    SUBCATEGORY_SOURCES,
    DEFAULT_WEIGHTS,
    ScoringResult,
)
from src.logic.summaries import top_city_summary, bottom_city_summary, scenario_summary


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
    bottom = results[-1]
    spread = top.total_score - bottom.total_score if len(results) > 1 else 0.0

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

        key_takeaway = (
            f"{top.city} currently leads with a total score of {top.total_score:.2f}, "
            f"outperforming {bottom.city} by {spread:.2f} points under this weighting profile."
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
                    '<p class="sw-insight-title">Trailing Candidate</p>'
                    f'<p class="sw-insight-body">{_plain_text(bottom_city_summary(bottom))}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        c1, c2, c3 = st.columns(3, gap="small")
        c1.metric("Leader", top.city, f"{top.total_score:.2f}")
        c2.metric("Trailer", bottom.city, f"{bottom.total_score:.2f}")
        c3.metric("Spread", f"{spread:.2f}", "best vs worst")
        st.info(scenario_summary(scenario_name, results))


def render_scoring_explainer_body() -> None:
    """Scoring methodology (no expander wrapper)."""
    st.markdown(
        """
**Weighted multi-criteria decision analysis (MCDA)** — each city is scored on **15**
subcategories in **5** themes. All scores use a **1–5** scale (**5** = best for
data-center siting).

**1 · Subcategory scores**  
Higher is always better for siting. Some inputs are inverted (e.g. *Tornado Frequency*:
high risk → low score).

**2 · Category score**  
Subcategories within each theme are averaged (missing values excluded).

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


def render_category_explainer_body() -> None:
    """Category reference (no expander wrapper)."""
    for cat in CATEGORIES:
        st.markdown(f"**{cat}** · default weight **{DEFAULT_WEIGHTS[cat]:.0%}**")
        for sub in SUBCATEGORIES.get(cat, []):
            tooltip = SUBCATEGORY_TOOLTIPS.get(sub, "")
            source = SUBCATEGORY_SOURCES.get(sub, "")
            src_link = f" · [source]({source})" if source else ""
            st.caption(f"• **{sub}** — {tooltip}{src_link}")
        st.markdown("")


def render_category_explainer() -> None:
    """Show each category with its subcategories and tooltips."""
    with st.expander("Category definitions", expanded=False):
        render_category_explainer_body()


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
                "Workbook not found in `data/`. Using the **built-in pilot** dataset."
            )

        st.markdown("**Notes & caveats**")
        for note in quality_notes:
            st.markdown(f"- {note}")

        st.caption(
            "To use your file: place **Data_Center_Site_Selector_RH.xlsx** in the "
            "`data/` folder and restart the app (or clear cache)."
        )


def render_future_features() -> None:
    """Show a roadmap panel for coming features."""
    with st.expander("Roadmap", expanded=False):
        st.markdown(
            """
| Direction | Status |
| --- | --- |
| Map integration (Folium / Mapbox) | Planned |
| AI narrative summary | Planned |
| Cooling-system sensitivity | Planned |
| CMIP6 climate detail | Planned |
| In-app workbook upload | Planned |
| PDF export | Planned |
| Sensitivity / Monte Carlo | Planned |
"""
        )
