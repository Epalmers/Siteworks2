"""
app.py – Siteworks: Data Center Site Selection Dashboard
=========================================================
CIVE-580: Applying AI in Environmental Engineering

Run with:
    streamlit run app.py
    python app.py          # same effect: starts Streamlit in your browser
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src` is importable.
_APP_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_APP_ROOT))

# If someone runs `python app.py` instead of `streamlit run app.py`, re-exec under
# Streamlit so the dashboard actually starts. When Streamlit loads this file,
# `streamlit` is already imported, so we skip this branch (avoids recursion).
if __name__ == "__main__" and "streamlit" not in sys.modules:
    import importlib.util

    if importlib.util.find_spec("streamlit") is None:
        print(
            "Streamlit is not installed for this Python interpreter:\n"
            f"  {sys.executable}\n\n"
            "From the project folder, install dependencies:\n"
            "  python -m pip install -r requirements.txt\n"
            "Or create a venv and install (recommended):\n"
            "  .\\setup.ps1\n",
            file=sys.stderr,
        )
        raise SystemExit(1)

    import subprocess

    rc = subprocess.call(
        [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    )
    raise SystemExit(rc)

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
    render_scoring_explainer_body,
    render_category_explainer_body,
    render_data_quality_panel,
    render_future_features,
)
from src.ui.styles import apply_global_styles, render_hero, render_scenario_banner
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

def _render_leader_strip(results):
    """Top three cities as compact metrics."""
    if not results:
        return
    n = min(3, len(results))
    cols = st.columns(n)
    medals = ("Leader", "2nd", "3rd")
    for i, col in enumerate(cols):
        r = results[i]
        with col:
            if i == 0:
                st.metric(
                    label=f"{medals[i]} · {r.city}",
                    value=f"{r.total_score:.2f}",
                    help="Highest weighted composite score.",
                )
            else:
                gap = r.total_score - results[0].total_score
                st.metric(
                    label=f"{medals[i]} · {r.city}",
                    value=f"{r.total_score:.2f}",
                    delta=f"{gap:+.2f} vs leader",
                    delta_color="inverse",
                    help="Gap to first place.",
                )


def main():
    apply_global_styles()

    city_data_base, quality_notes, from_workbook = _load()
    weights, scenario_name, drought_mode, future_climate_mode = render_sidebar()

    city_data = city_data_base
    if drought_mode:
        city_data = apply_drought_scenario(city_data)
    if future_climate_mode:
        city_data = apply_future_climate_scenario(city_data)

    results = rank_cities(city_data, weights)

    render_hero(from_workbook=from_workbook)

    if drought_mode or future_climate_mode:
        pretty = []
        if drought_mode:
            pretty.append("Drought year (−20% water-related scores)")
        if future_climate_mode:
            pretty.append("2050 climate shift")
        render_scenario_banner(pretty)

    st.markdown("#### Snapshot")
    _render_leader_strip(results)

    tab_overview, tab_compare, tab_data, tab_about = st.tabs(
        ["Overview", "Compare", "Data", "About"]
    )

    with tab_overview:
        with st.container(border=True):
            st.markdown("##### Rankings")
            st.caption(
                "Weighted **1–5** composite (**5** = best for siting). "
                "Adjust priorities in the sidebar to reshuffle results."
            )
            render_ranking_table(results)

        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.plotly_chart(total_score_bar(results), width="stretch")
        with c2:
            st.plotly_chart(radar_chart(results), width="stretch")

        st.plotly_chart(category_score_grouped_bar(results), width="stretch")

        render_summary_panel(results, scenario_name)

        with st.expander("How scoring works", expanded=False):
            render_scoring_explainer_body()

        with st.expander("Category definitions", expanded=False):
            render_category_explainer_body()

    with tab_compare:
        with st.container(border=True):
            st.markdown("##### Head-to-head")
            st.caption(
                "Pick two cities for category scores, deltas, and subcategory detail."
            )
            render_comparison_view(city_data, results)

    with tab_data:
        with st.container(border=True):
            st.markdown("##### Subcategory explorer")
            st.caption(
                "Raw **1–5** sub-scores and measurements. "
                "**5** always means better for data-center siting."
            )

            selected_city = st.selectbox(
                "City",
                options=list(city_data.keys()),
                key="data_explorer_city",
            )

            if selected_city:
                cd = city_data[selected_city]
                st.markdown(f"**{selected_city}** — metric breakdown")
                render_subcategory_table(selected_city, cd, _scoring_module)

        render_data_quality_panel(quality_notes, from_workbook)
        render_future_features()

    with tab_about:
        with st.container(border=True):
            st.markdown("##### About Siteworks")
            st.markdown(
                """
**Siteworks** is a weighted MCDA dashboard for **data center site selection**,
built for **CIVE-580: Applying AI in Environmental Engineering**.

**Driving question**  
*Is this location sustainable — or will it face acute water or climate stress?*

**Pilot cities**  
Oklahoma City · Boston · Denver · Houston · Gainesville

**Five themes**

| Theme | Default weight | Focus |
| --- | --- | --- |
| Hydrological & Regulatory Risk | 25% | Water scarcity, precipitation, reuse |
| Climate & Operational Physics | 30% | Cooling load, humidity, grid carbon |
| Economic & Social Impact | 15% | Power rates, water cost, equity |
| Natural Hazards | 20% | Flood, tornado, wildlife, winter |
| Biodiversity | 10% | Protected-area constraints |

**Scale**  
All metrics are **1 (worst) → 5 (best)** for siting. High *risk* metrics are inverted so **5** still means *better*.

**How to use**  
Use the sidebar weights and scenario toggles, compare two cities on **Compare**, and
inspect drivers on **Data**.

**Limits**  
Five-city pilot; public-data estimates; not a substitute for professional engineering.

**Sources**  
`Data_Center_Site_Selector_RH.xlsx` in `data/` · methodology docs in repo README.
"""
            )


if __name__ == "__main__":
    main()
