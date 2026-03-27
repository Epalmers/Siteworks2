"""
sidebar.py – Streamlit sidebar controls for Siteworks.

Renders weight sliders, scenario presets, and supplementary controls.
Returns the current normalised weights to the caller.
"""

from typing import Dict, Tuple

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


def render_sidebar() -> Tuple[Dict[str, float], str, bool, bool]:
    """
    Render the sidebar and return:
        (normalised_weights, scenario_name, drought_mode, future_climate_mode)
    """
    st.sidebar.title("⚙️ Siteworks Controls")

    # --- Scenario preset ---
    st.sidebar.markdown("### 🎯 Scenario Preset")
    scenario_name = st.sidebar.selectbox(
        "Apply a weight preset",
        options=list(SCENARIO_WEIGHTS.keys()),
        index=0,
        help="Choose a named scenario to auto-set the category weights below.",
    )
    if scenario_name != "Default":
        st.sidebar.caption(SCENARIO_DESCRIPTIONS[scenario_name])

    # Determine starting weights from scenario
    preset_weights = SCENARIO_WEIGHTS[scenario_name]

    # --- Weight sliders ---
    st.sidebar.markdown("### 🎚️ Category Weights")
    st.sidebar.caption(
        "Adjust how much each category counts toward the final score. "
        "Weights are normalised automatically so they always sum to 1.0."
    )

    raw_weights: Dict[str, float] = {}
    for cat in CATEGORIES:
        default_val = preset_weights.get(cat, DEFAULT_WEIGHTS[cat])
        raw_weights[cat] = st.sidebar.slider(
            label=_SHORT_LABELS.get(cat, cat),
            min_value=0.0,
            max_value=1.0,
            value=float(round(default_val, 2)),
            step=0.05,
            key=f"weight_{cat}",
            help=f"Raw weight for: {cat}",
        )

    # Normalise
    try:
        norm_weights = normalize_weights(raw_weights)
    except ValueError:
        st.sidebar.error("All weights are zero – resetting to defaults.")
        norm_weights = reset_to_defaults()

    # Show normalised values
    with st.sidebar.expander("📊 Normalised weights (sum = 1.0)", expanded=False):
        for cat in CATEGORIES:
            pct = norm_weights.get(cat, 0.0) * 100
            st.caption(f"{_SHORT_LABELS.get(cat, cat)}: **{pct:.1f}%**")

    # Validate
    ok, issues = validate_weights(norm_weights)
    if not ok:
        for issue in issues:
            st.sidebar.warning(issue)

    # Reset button
    if st.sidebar.button("🔄 Reset to Defaults"):
        st.rerun()

    # --- Scenario toggles ---
    st.sidebar.markdown("### 🔬 What-If Scenarios")
    st.sidebar.caption("⚠️ Prototype features – adjustments are approximate.")
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
    st.sidebar.caption(
        "Siteworks v1.0 · CIVE-580 · "
        "Scores: 1 (worst) – 5 (best)"
    )

    return norm_weights, scenario_name, drought_mode, future_climate
