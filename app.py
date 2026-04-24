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
    city_color,
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
from src.ui.zoning_map import render_industrial_zoning_map
from src.ui.styles import (
    apply_global_styles,
    render_hero,
    render_scenario_banner,
    render_kpi_strip,
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

def _render_leader_strip(results):
    """Render top-3 ranking cards with clear visual hierarchy."""
    if not results:
        return
    cards = []
    top = results[: min(3, len(results))]
    for i, r in enumerate(top):
        role = "Leader" if i == 0 else ("2nd" if i == 1 else "3rd")
        if i == 0:
            avg = sum(x.total_score for x in results) / len(results)
            sub = f"+{(r.total_score - avg):.2f} above average"
            klass = "is-leader"
        else:
            avg = sum(x.total_score for x in results) / len(results)
            sub = f"{(r.total_score - avg):+.2f} vs average"
            klass = "is-secondary"
        dot = city_color(r.city)
        cards.append(
            (
                f'<div class="sw-snapshot-card {klass}">'
                f'<p class="sw-snapshot-role">{role}</p>'
                f'<p class="sw-snapshot-city"><span class="sw-city-dot" style="background:{dot};"></span>{r.city}</p>'
                f'<p class="sw-snapshot-score">{r.total_score:.2f}</p>'
                f'<p class="sw-snapshot-sub">{sub}</p>'
                "</div>"
            )
        )
    st.markdown(
        f'<div class="sw-snapshot-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def _render_top_summary(results, from_workbook, drought_mode, future_climate_mode):
    """Render hero, KPI strip, and snapshot row."""
    render_hero(from_workbook=from_workbook)
    top = results[0]
    runner_up = results[1] if len(results) > 1 else None
    spread = top.total_score - results[-1].total_score if len(results) > 1 else 0.0
    gap_to_second = (top.total_score - runner_up.total_score) if runner_up else 0.0
    active_mods = int(drought_mode) + int(future_climate_mode)
    render_kpi_strip(
        [
            {
                "label": "Top Ranked City",
                "value": top.city,
                "sub": f"Score {top.total_score:.2f}",
            },
            {
                "label": "Leader Margin",
                "value": f"{gap_to_second:+.2f}",
                "sub": "vs second-ranked city",
            },
            {
                "label": "Score Spread",
                "value": f"{spread:.2f}",
                "sub": "best to worst",
            },
            {
                "label": "Active Modifiers",
                "value": str(active_mods),
                "sub": "what-if scenarios enabled",
            },
        ]
    )

    if drought_mode or future_climate_mode:
        pretty = []
        if drought_mode:
            pretty.append("Drought year (−20% water-related scores)")
        if future_climate_mode:
            pretty.append("2050 climate shift")
        render_scenario_banner(pretty)

    st.markdown("#### Snapshot")
    _render_leader_strip(results)
    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)


def _render_overview_tab(results, scenario_name):
    """Render summary -> comparison -> breakdown -> interpretation flow."""
    with st.container(border=True):
        st.markdown("##### Rankings")
        st.caption(
            "Weighted composite score (**1–5**, where **5** is most suitable). "
            "Adjust priorities in the sidebar to update the ranking in real time."
        )
        render_ranking_table(results)

    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)
    city_options = [r.city for r in results]
    default_cities = city_options[: min(3, len(city_options))]

    # Row 2: Overall score + Radar (side-by-side)
    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        with st.container(border=True):
            st.markdown("##### Overall Score")
            st.plotly_chart(total_score_bar(results), width="stretch")

    with c_right:
        with st.container(border=True):
            st.markdown("##### Category Profile (Radar)")
            radar_cities = st.multiselect(
                "Radar Cities",
                options=city_options,
                default=default_cities,
                max_selections=3,
                key="radar_panel_cities",
                help="Select 2-3 cities to compare category profiles.",
            )
            if len(radar_cities) < 2:
                st.info("Select at least 2 cities to render the radar comparison.")
            else:
                selected_results = [r for r in results if r.city in radar_cities]
                st.plotly_chart(radar_chart(selected_results), width="stretch")

    # Row 3: Full-width grouped category comparison
    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        c_title, c_control = st.columns([2.2, 1.3], gap="small")
        c_title.markdown("##### Category Comparison")
        with c_control:
            selected_cities = st.multiselect(
                "Focus Cities",
                options=city_options,
                default=default_cities,
                max_selections=3,
                key="radar_compare_cities",
                help="Select up to 3 cities to emphasize in this chart.",
                label_visibility="collapsed",
                placeholder="Focus cities",
            )
        st.plotly_chart(
            category_score_grouped_bar(
                results,
                emphasis_cities=selected_cities if len(selected_cities) >= 2 else None,
            ),
            width="stretch",
        )

    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("##### Industrial Zoning (map)")
        st.caption(
            "Municipal **industrial** (or land-use) parcels from the pilot shapefiles in "
            "`data/Zoning_Spatial_Data/`. Toggle cities in the layer control; colours match "
            "the dashboard city palette. Large metros may show a **sample** of parcels for performance."
        )
        map_cities = st.multiselect(
            "Cities to show on map",
            options=city_options,
            default=city_options,
            key="zoning_map_city_pick",
            help="Industrial / industrial-use polygons from the packaged .zip shapefiles by city.",
        )
        render_industrial_zoning_map(map_cities)

    st.markdown("<div class='sw-spacer'></div>", unsafe_allow_html=True)
    render_summary_panel(results, scenario_name)

    with st.expander("How scoring works", expanded=False):
        render_scoring_explainer_body()

    with st.expander("Category definitions", expanded=False):
        render_category_explainer_body()


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
    if not results:
        st.error("No ranking results available. Check input data and refresh.")
        return

    _render_top_summary(results, from_workbook, drought_mode, future_climate_mode)

    tab_overview, tab_compare, tab_data, tab_about = st.tabs(
        ["Overview", "Compare", "Data", "About"]
    )

    with tab_overview:
        _render_overview_tab(results, scenario_name)

    with tab_compare:
        with st.container(border=True):
            st.markdown("##### Head-to-Head Comparison")
            st.caption(
                "Pick two cities for category scores, deltas, and subcategory detail."
            )
            render_comparison_view(city_data, results)

    with tab_data:
        with st.container(border=True):
            st.markdown("##### Subcategory Explorer")
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
