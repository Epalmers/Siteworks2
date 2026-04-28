"""
sidebar.py – Streamlit sidebar controls for Siteworks.

Renders weight sliders, scenario presets, and supplementary controls.
Returns the current normalised weights to the caller.
"""

from typing import Dict, Optional, Tuple

import streamlit as st

from src.data.schema import CATEGORIES, DEFAULT_WEIGHTS
from src.logic.scoring import normalize_weights, reset_to_defaults
from src.logic.scenarios import SCENARIO_WEIGHTS, SCENARIO_DESCRIPTIONS
from src.logic.validation import validate_weights

# Short labels for sliders
_SHORT_LABELS: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "💧 Hydro & Regulatory",
    "Climate & Operational Physics":  "🌡️ Climate & Grid",
    "Economic & Social Impact":       "💰 Economic & Social",
    "Natural Hazards":                "⚡ Natural Hazards",
    "Biodiversity":                   "🌿 Biodiversity",
}


def render_sidebar(
    workbook_default_weights: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, float], str, bool, bool]:
    """
    Render the sidebar and return:
        (normalised_weights, scenario_name, drought_mode, future_climate_mode)

    If **workbook_default_weights** is provided (from the **Account Weights** sheet),
    the **Default** scenario uses those values instead of app defaults.
    """
    st.sidebar.markdown("## Controls")
    st.sidebar.caption("Weights & scenarios drive all rankings and charts.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Preset")
    scenario_name = st.sidebar.selectbox(
        "Scenario",
        options=list(SCENARIO_WEIGHTS.keys()),
        index=0,
        key="scenario_preset",
        label_visibility="collapsed",
        help="Sets starting weights; you can still fine-tune sliders below.",
    )
    if scenario_name != "Default":
        st.sidebar.caption(SCENARIO_DESCRIPTIONS[scenario_name])

    # Determine starting weights from scenario
    if (
        scenario_name == "Default"
        and workbook_default_weights
        and all(c in workbook_default_weights for c in CATEGORIES)
    ):
        preset_weights = workbook_default_weights
    else:
        preset_weights = SCENARIO_WEIGHTS[scenario_name]

    # Keep slider state in sync when preset changes.
    if "_last_scenario_preset" not in st.session_state:
        st.session_state["_last_scenario_preset"] = scenario_name
        for cat in CATEGORIES:
            st.session_state[f"weight_{cat}"] = float(
                round(preset_weights.get(cat, DEFAULT_WEIGHTS[cat]), 2)
            )
    elif st.session_state["_last_scenario_preset"] != scenario_name:
        st.session_state["_last_scenario_preset"] = scenario_name
        for cat in CATEGORIES:
            st.session_state[f"weight_{cat}"] = float(
                round(preset_weights.get(cat, DEFAULT_WEIGHTS[cat]), 2)
            )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Category weights")
    st.sidebar.caption("Normalized to sum to **1.0** automatically.")

    raw_weights: Dict[str, float] = {}
    for cat in CATEGORIES:
        default_val = preset_weights.get(cat, DEFAULT_WEIGHTS[cat])
        slider_key = f"weight_{cat}"
        raw_weights[cat] = st.sidebar.slider(
            label=_SHORT_LABELS.get(cat, cat),
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.get(slider_key, round(default_val, 2))),
            step=0.01,
            key=slider_key,
            help=f"Raw weight for: {cat}",
        )

    # Normalise
    try:
        norm_weights = normalize_weights(raw_weights)
    except ValueError:
        st.sidebar.error("All weights are zero – resetting to defaults.")
        norm_weights = reset_to_defaults()

    with st.sidebar.expander("Normalized % (detail)", expanded=False):
        for cat in CATEGORIES:
            pct = norm_weights.get(cat, 0.0) * 100
            st.caption(f"{_SHORT_LABELS.get(cat, cat)}: **{pct:.1f}%**")

    # Validate
    ok, issues = validate_weights(norm_weights)
    if not ok:
        for issue in issues:
            st.sidebar.warning(issue)

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Preset", use_container_width=True, help="Reset sliders to selected preset"):
        for cat in CATEGORIES:
            st.session_state[f"weight_{cat}"] = float(
                round(preset_weights.get(cat, DEFAULT_WEIGHTS[cat]), 2)
            )
        st.rerun()
    if c2.button("Default", use_container_width=True, help="Reset sliders to app defaults"):
        st.session_state["scenario_preset"] = "Default"
        st.session_state["_last_scenario_preset"] = "Default"
        for cat in CATEGORIES:
            st.session_state[f"weight_{cat}"] = float(round(DEFAULT_WEIGHTS[cat], 2))
        st.rerun()

    if st.sidebar.button("Refresh data", use_container_width=True, help="Clear cached workbook and re-read files"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### What-if modifiers")
    st.sidebar.caption("Approximate sensitivity — not predictive models.")
    drought_mode = st.sidebar.checkbox(
        "🌵 Drought Year (–20% water scores)",
        value=False,
        help="Simulates a drought year by reducing water-related subcategory scores.",
    )
    future_climate = st.sidebar.checkbox(
        "🌍 2050 Climate Shift",
        value=False,
        help="Applies projected 2050 climate changes (CMIP6-inspired estimates).",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("DCS Dashboard · Scale 1–5 (5 = best for siting)")

    return norm_weights, scenario_name, drought_mode, future_climate
