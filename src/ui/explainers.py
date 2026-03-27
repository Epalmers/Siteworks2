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
    st.markdown("### 📖 What This Means")

    if not results:
        st.warning("No results to summarise.")
        return

    top = results[0]
    bottom = results[-1]

    with st.container():
        st.markdown(f"**Top-ranked city:** {top_city_summary(top)}")
        st.markdown("---")
        st.markdown(f"**Lowest-ranked city:** {bottom_city_summary(bottom)}")
        st.markdown("---")
        st.info(scenario_summary(scenario_name, results))


def render_scoring_explainer() -> None:
    """Explain the scoring methodology in plain language."""
    with st.expander("ℹ️ How Does the Scoring Work?", expanded=False):
        st.markdown(
            """
**Siteworks uses a Weighted Multi-Criteria Decision Analysis (MCDA) model.**

Each city is scored on 15 subcategory metrics grouped into 5 categories.
All scores are on a **1–5 scale** (5 = best for data-center siting).

**Step 1 – Subcategory scores**  
Each metric is evaluated and scored 1–5.  Higher always means "better for building 
a data center here."  Some metrics are inverted: for example, *Tornado Frequency* 
scores 1 in high-tornado areas and 5 in safe areas.

**Step 2 – Category average**  
The subcategory scores within each category are averaged.

**Step 3 – Weighted total**  
```
Total = (Hydro × w₁) + (Climate × w₂) + (Economic × w₃) + (Hazards × w₄) + (Bio × w₅)
```
Weights always sum to 1.0 and can be adjusted using the sliders in the sidebar.

**Step 4 – Ranking**  
Cities are ranked from highest total score (most suitable) to lowest.

---
*This is a decision-support tool.  Use it alongside site visits, legal review, 
and engineering studies before making final decisions.*
"""
        )


def render_category_explainer() -> None:
    """Show each category with its subcategories and tooltips."""
    with st.expander("📂 Category & Subcategory Definitions", expanded=False):
        for cat in CATEGORIES:
            st.markdown(f"**{cat}** *(default weight: {DEFAULT_WEIGHTS[cat]:.0%})*")
            for sub in SUBCATEGORIES.get(cat, []):
                tooltip = SUBCATEGORY_TOOLTIPS.get(sub, "")
                source = SUBCATEGORY_SOURCES.get(sub, "")
                src_link = f" · [source]({source})" if source else ""
                st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;• **{sub}**: {tooltip}{src_link}")
            st.markdown("")


def render_data_quality_panel(
    quality_notes: List[str],
    from_workbook: bool,
) -> None:
    """Show data source and quality notes."""
    with st.expander("⚠️ Data Quality & Assumptions", expanded=False):
        if from_workbook:
            st.success("Data loaded from Excel workbook.")
        else:
            st.warning(
                "Excel workbook not found in `/data/`.  "
                "Using **built-in pilot dataset** with estimates from public sources."
            )

        st.markdown("**Known assumptions and limitations:**")
        for note in quality_notes:
            st.markdown(f"- {note}")

        st.markdown(
            """
---
**To use your own data:**  
Place `Data_Center_Site_Selector_RH.xlsx` in the `/data/` folder and restart the app.
The parser will automatically read the *Site Selector Data - edited* sheet.
"""
        )


def render_future_features() -> None:
    """Show a roadmap panel for coming features."""
    with st.expander("🚀 Coming Next (Roadmap)", expanded=False):
        st.markdown(
            """
The following features are planned for future releases based on the project roadmap:

| Feature | Status |
|---|---|
| Map integration (Folium / Mapbox) | 🔜 Prototype Placeholder |
| AI-generated narrative summary | 🔜 Prototype Placeholder |
| Recycled water yes/no toggle | 🔜 Prototype Placeholder |
| Cooling type sensitivity (air vs. water) | 🔜 Prototype Placeholder |
| Full 2050 CMIP6 climate projections | 🔜 Prototype Placeholder |
| Upload custom city data | 🔜 Planned |
| Export to PDF report | 🔜 Planned |
| Sensitivity / Monte Carlo analysis | 🔜 Planned |

*Want to contribute?  See the README for architecture notes.*
"""
        )
