"""
explainers.py – Tooltips, plain-language panels, and data transparency views.
"""

from typing import Dict, List

import streamlit as st

from src.data.schema import (
    CATEGORIES,
    SUBCATEGORIES,
    SUBCATEGORY_TOOLTIPS,
    SUBCATEGORY_SOURCES,
    DEFAULT_WEIGHTS,
    CityData,
    ScoringResult,
)
from src.logic.summaries import top_city_summary, bottom_city_summary, scenario_summary
from src.data.loader import DATA_QUALITY_NOTES


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

    with st.container(border=True):
        st.markdown("##### Interpretation")
        a, b = st.columns(2, gap="medium")
        with a:
            st.markdown("**Leading candidate**")
            st.caption(top_city_summary(top))
        with b:
            st.markdown("**Trailing candidate**")
            st.caption(bottom_city_summary(bottom))
        st.markdown("")
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
