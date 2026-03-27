"""
app.py – Siteworks: Data Center Site Selection Dashboard
=========================================================
CIVE-580: Applying AI in Environmental Engineering

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src` is importable.
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# --- Page config (must be first Streamlit call) ---
st.set_page_config(
    page_title="Siteworks – Data Center Site Selector",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.data.loader import load_city_data
from src.logic.scoring import rank_cities
from src.logic.scenarios import apply_drought_scenario, apply_future_climate_scenario
from src.ui.sidebar import render_sidebar
from src.ui.charts import (
    total_score_bar,
    category_score_grouped_bar,
    radar_chart,
)
from src.ui.tables import render_ranking_table, render_subcategory_table
from src.ui.compare import render_comparison_view
from src.ui.explainers import (
    render_summary_panel,
    render_scoring_explainer,
    render_category_explainer,
    render_data_quality_panel,
    render_future_features,
)
import src.logic.scoring as _scoring_module


# ---------------------------------------------------------------------------
# Load data (cached so it doesn't re-parse on every interaction)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading city data …")
def _load():
    return load_city_data()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

def main():
    # --- Load data ---
    city_data_base, quality_notes, from_workbook = _load()

    # --- Sidebar controls ---
    weights, scenario_name, drought_mode, future_climate_mode = render_sidebar()

    # --- Apply scenario modifiers ---
    city_data = city_data_base
    if drought_mode:
        city_data = apply_drought_scenario(city_data)
    if future_climate_mode:
        city_data = apply_future_climate_scenario(city_data)

    # --- Score & rank ---
    results = rank_cities(city_data, weights)

    # --- Header ---
    st.markdown(
        """
        <h1 style='margin-bottom:0'>🏗️ Siteworks</h1>
        <p style='color:grey;font-size:1.1em;margin-top:4px'>
        Data Center Site Selection Dashboard &nbsp;·&nbsp; CIVE-580
        </p>
        """,
        unsafe_allow_html=True,
    )

    if drought_mode or future_climate_mode:
        active = []
        if drought_mode:
            active.append("🌵 Drought Year")
        if future_climate_mode:
            active.append("🌍 2050 Climate Shift")
        st.warning(f"⚠️ Active scenario modifiers: {', '.join(active)}")

    # --- Tab navigation ---
    tab_overview, tab_compare, tab_data, tab_about = st.tabs([
        "📊 Rankings & Overview",
        "🆚 Compare Cities",
        "🔍 Data Explorer",
        "ℹ️ About & Methodology",
    ])

    # ==========================================================================
    # TAB 1 – Overview
    # ==========================================================================
    with tab_overview:
        st.markdown("### 🏆 City Rankings")
        st.caption(
            "Cities are ranked by their **weighted sustainability score** (1–5 scale). "
            "Adjust weights in the sidebar to see how priorities change the ranking."
        )

        # Ranked table
        render_ranking_table(results)

        # Charts
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.plotly_chart(total_score_bar(results), use_container_width=True)
        with col_right:
            st.plotly_chart(
                radar_chart(results),
                use_container_width=True,
            )

        st.plotly_chart(
            category_score_grouped_bar(results), use_container_width=True
        )

        # Summary panel
        render_summary_panel(results, scenario_name)

        # Methodology explainers
        render_scoring_explainer()
        render_category_explainer()

    # ==========================================================================
    # TAB 2 – Compare Cities
    # ==========================================================================
    with tab_compare:
        st.markdown("### 🆚 City Comparison")
        st.caption(
            "Select any two cities to see a detailed side-by-side comparison "
            "of their category and subcategory scores."
        )
        render_comparison_view(city_data, results)

    # ==========================================================================
    # TAB 3 – Data Explorer
    # ==========================================================================
    with tab_data:
        st.markdown("### 🔍 Data Explorer")
        st.caption(
            "Inspect the underlying subcategory scores for any city. "
            "All scores are on a 1–5 scale (5 = best for data-center siting)."
        )

        selected_city = st.selectbox(
            "Select a city to inspect",
            options=list(city_data.keys()),
            key="data_explorer_city",
        )

        if selected_city:
            cd = city_data[selected_city]
            st.markdown(f"#### Subcategory scores for **{selected_city}**")
            render_subcategory_table(selected_city, cd, _scoring_module)

        render_data_quality_panel(quality_notes, from_workbook)
        render_future_features()

    # ==========================================================================
    # TAB 4 – About
    # ==========================================================================
    with tab_about:
        st.markdown("### ℹ️ About Siteworks")
        st.markdown(
            """
**Siteworks** is a weighted multi-criteria decision analysis (MCDA) dashboard 
for data center site selection.  It was built as a class project for 
**CIVE-580: Applying AI in Environmental Engineering**.

#### Core question
> *"Is this site sustainable, or will it run out of water in 10 years?"*

#### Five pilot cities
Oklahoma City · Boston · Denver · Houston · Gainesville

#### Five sustainability categories
| Category | Default Weight | Focus |
|---|---|---|
| Hydrological & Regulatory Risk | 25% | Water scarcity, precipitation, recycled water |
| Climate & Operational Physics | 30% | Cooling efficiency, humidity, grid carbon |
| Economic & Social Impact | 15% | Electricity rates, water costs, equity |
| Natural Hazards | 20% | Flood, tornado, wildlife, winter weather |
| Biodiversity | 10% | Protected land proximity |

#### Scoring scale
All metrics are scored **1 (worst) to 5 (best)** for data-center siting.
Higher-risk metrics (e.g., tornado frequency, flood risk) are scored inversely.

#### How to use
1. Use the **sidebar sliders** to adjust category weights for your priorities.
2. Pick a **Scenario Preset** for quick what-if analysis.
3. Use the **Compare Cities** tab to drill into two cities side by side.
4. Use the **Data Explorer** tab to inspect underlying subcategory scores.
5. Check the **Data Quality & Assumptions** panel for caveats.

#### Limitations
- Pilot dataset covers 5 cities only.
- Scores are estimates based on public data; site-specific measurements may differ.
- This is a decision-support prototype – not a substitute for professional engineering review.

#### Source files
| File | Role |
|---|---|
| `Data_Center_Site_Selector_RH.xlsx` | Primary scoring data (place in `/data/`) |
| `CIVE580 Algorithms for AI.docx` | Scoring logic specification |
| `Project_Roadmap.docx` | Feature roadmap |
| `CIVE 580 Project MAA.xlsx` | Future-expansion template (not parsed) |
| `Data-Center-Site-Selector-A-Vibe-Coding-Approach.pptx` | UX & product direction |
"""
        )


if __name__ == "__main__":
    main()
