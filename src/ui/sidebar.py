"""
sidebar.py – Streamlit sidebar controls for Siteworks.

Renders the Decision Mode picker, the category-weight sliders (with
+/- nudge buttons on either side), and the What-if Scenario checkboxes.
Returns the active weights and scenario flags to the caller.

UX rules implemented here:
  • Only "Custom Weights" mode lets the user move the sliders.
  • All other modes lock the sliders AND nudge buttons to their preset
    values (rendered with `disabled=True`).
  • In "Custom Weights" mode, a live "Used / Remaining" indicator shows
    the running sum, and the **Apply Weights** button is disabled until
    the sliders sum to exactly 1.00 (within tolerance). Until the user
    clicks Apply, the rankings continue to use the previously committed
    weights.
  • Each weight slider gets a [-] button to its left and a [+] button to
    its right. Clicking nudges the weight by ±0.01 (clamped to 0.00–1.00).
    Buttons fire as Streamlit on_click callbacks so they can safely modify
    the slider's session_state value before the widget is rebuilt.

Streamlit note: any button that needs to modify a widget's session-state
value MUST do so in an ``on_click=`` callback. Writing
``st.session_state[widget_key] = ...`` from inline ``if button:`` code
after the widget has been instantiated will raise StreamlitAPIException.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import streamlit as st

# Project-root assets (PNG preferred if you add `assets/siteworks_logo.png`).
_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_LOGO_PNG = _ASSETS_DIR / "siteworks_logo.png"
_LOGO_SVG = _ASSETS_DIR / "siteworks_logo.svg"

from src.data.schema import CATEGORIES, DEFAULT_WEIGHTS
from src.logic.scenarios import (
    SCENARIO_WEIGHTS,
    SCENARIO_DESCRIPTIONS,
    CUSTOM_MODE_NAME,
)
from src.logic.validation import validate_weights

# Tolerance when checking whether custom weights sum to exactly 1.0.
_SUM_TOLERANCE = 1e-3

# How much each +/- click changes a weight (matches the slider's step).
_NUDGE_STEP = 0.01

# Short labels for sliders
_SHORT_LABELS: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "💧 Hydro & Regulatory",
    "Climate & Operational Physics":  "🌡️ Climate & Grid",
    "Economic & Social Impact":       "💰 Economic & Social",
    "Natural Hazards":                "⚡ Natural Hazards",
    "Biodiversity":                   "🌿 Biodiversity",
}


# ---------------------------------------------------------------------------
# Button callbacks (must be module-level functions for Streamlit on_click)
# ---------------------------------------------------------------------------

def _apply_weights_callback() -> None:
    """Commit the current slider values as the active weights."""
    committed: Dict[str, float] = {}
    for cat in CATEGORIES:
        key = f"weight_slider_{cat}"
        committed[cat] = float(st.session_state.get(key, DEFAULT_WEIGHTS[cat]))
    st.session_state["_custom_committed"] = committed


def _reset_to_defaults_callback() -> None:
    """Reset both the sliders and the committed weights to app defaults."""
    for cat in CATEGORIES:
        st.session_state[f"weight_slider_{cat}"] = float(DEFAULT_WEIGHTS[cat])
    st.session_state["_custom_committed"] = DEFAULT_WEIGHTS.copy()


def _refresh_data_callback() -> None:
    """Clear the workbook cache so the next run re-reads the .xlsx file."""
    st.cache_data.clear()


def _nudge_weight_callback(category: str, direction: int) -> None:
    """
    Nudge one weight slider up (direction=+1) or down (direction=-1) by
    one ``_NUDGE_STEP`` (currently 0.01). Clamped to the [0.0, 1.0] range.
    """
    key = f"weight_slider_{category}"
    current = float(st.session_state.get(key, DEFAULT_WEIGHTS[category]))
    new_val = current + direction * _NUDGE_STEP
    # Clamp and round to avoid floating-point drift like 0.5300000000000001.
    new_val = max(0.0, min(1.0, round(new_val, 2)))
    st.session_state[key] = new_val


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_sidebar(
    workbook_default_weights: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, float], str, Dict[str, bool]]:
    """
    Render the sidebar and return:
        (weights, decision_mode_name, scenario_flags)

    where ``scenario_flags`` is a dict like::

        {"drought": bool, "flood": bool, "wildfire": bool, "tech_boom": bool}

    If **workbook_default_weights** is provided (from the workbook's
    *Account Weights* sheet), Custom Weights starts from those values
    on first load instead of the hard-coded app defaults.
    """
    # Migrate any session state from older versions that used "Default"
    # or contained the deprecated "Grid Stress" / "2050 Climate" scenarios.
    saved = st.session_state.get("scenario_preset")
    if saved and saved not in SCENARIO_WEIGHTS:
        st.session_state["scenario_preset"] = CUSTOM_MODE_NAME

    _logo_path: Optional[Path] = None
    if _LOGO_PNG.is_file():
        _logo_path = _LOGO_PNG
    elif _LOGO_SVG.is_file():
        _logo_path = _LOGO_SVG
    if _logo_path is not None:
        st.sidebar.image(str(_logo_path), use_container_width=True)

    st.sidebar.markdown("## Controls")
    st.sidebar.caption(
        "Two independent controls drive the rankings:  \n"
        "• **Decision Mode** = how much each theme matters (your priorities)  \n"
        "• **What-if Scenarios** = how conditions change in the real world"
    )

    # ---- Decision Mode ----
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Decision Mode")
    st.sidebar.caption("Sets the weights — how much each category counts toward the score.")
    scenario_name = st.sidebar.selectbox(
        "Mode",
        options=list(SCENARIO_WEIGHTS.keys()),
        index=0,
        key="scenario_preset",
        label_visibility="collapsed",
        help=(
            f"**{CUSTOM_MODE_NAME}** lets you set weights manually. "
            "Other modes use fixed weights designed for specific priorities."
        ),
    )
    if scenario_name in SCENARIO_DESCRIPTIONS:
        st.sidebar.caption(SCENARIO_DESCRIPTIONS[scenario_name])

    is_custom = scenario_name == CUSTOM_MODE_NAME

    # ---- Resolve the weights the sliders should reflect this run ----
    starting_weights = _resolve_starting_weights(scenario_name, workbook_default_weights)
    _sync_slider_state(scenario_name, starting_weights)

    # ---- Render the sliders with +/- nudge buttons ----
    st.sidebar.markdown("### Category weights")
    if is_custom:
        st.sidebar.caption(
            "Drag sliders or use the **−/+** buttons (±0.01) for fine-tuning. "
            "Weights must sum to **1.00**."
        )
    else:
        st.sidebar.info(
            f"🔒 Switch to **{CUSTOM_MODE_NAME}** to adjust these sliders."
        )

    draft_weights: Dict[str, float] = {}
    for cat in CATEGORIES:
        slider_key = f"weight_slider_{cat}"
        current_val = float(
            st.session_state.get(slider_key, starting_weights.get(cat, 0.0))
        )

        # Label sits above the row so the slider has the full width below it.
        st.sidebar.markdown(
            f"<div class='sw-weight-label'>{_SHORT_LABELS.get(cat, cat)}</div>",
            unsafe_allow_html=True,
        )

        # Three columns: [-] | slider | [+]
        # Narrow side columns keep the slider readable in the sidebar.
        col_minus, col_slider, col_plus = st.sidebar.columns(
            [1, 6, 1], gap="small", vertical_alignment="center"
        )

        with col_minus:
            st.button(
                "−",
                key=f"weight_minus_{cat}",
                on_click=_nudge_weight_callback,
                args=(cat, -1),
                disabled=(not is_custom) or (current_val <= 0.0),
                use_container_width=True,
                help=f"Decrease {cat} by 0.01",
            )

        with col_slider:
            val = st.slider(
                label=_SHORT_LABELS.get(cat, cat),
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                disabled=not is_custom,
                key=slider_key,
                label_visibility="collapsed",
                help=f"Weight for: {cat}",
            )
            draft_weights[cat] = float(val)

        with col_plus:
            st.button(
                "+",
                key=f"weight_plus_{cat}",
                on_click=_nudge_weight_callback,
                args=(cat, +1),
                disabled=(not is_custom) or (current_val >= 1.0),
                use_container_width=True,
                help=f"Increase {cat} by 0.01",
            )

    # ---- Custom mode: budget indicator + Apply / Reset buttons ----
    if is_custom:
        active_weights = _render_custom_apply_controls(draft_weights)
    else:
        active_weights = dict(starting_weights)

    # ---- Weight Summary panel (renamed from "Normalized %") ----
    with st.sidebar.expander("Weight Summary", expanded=False):
        st.caption("Currently applied weights, shown as percentages of the total.")
        for cat in CATEGORIES:
            pct = active_weights.get(cat, 0.0) * 100.0
            st.caption(f"{_SHORT_LABELS.get(cat, cat)}: **{pct:.1f}%**")
        total_pct = sum(active_weights.values()) * 100.0
        st.caption(f"**Total: {total_pct:.1f}%**")

    # ---- Backstop: validate (locked presets are always valid by construction) ----
    ok, issues = validate_weights(active_weights)
    if not ok:
        for issue in issues:
            st.sidebar.warning(issue)

    # ---- Refresh data ----
    st.sidebar.button(
        "🔄 Refresh data",
        on_click=_refresh_data_callback,
        use_container_width=True,
        help="Clear cached workbook and re-read files",
    )

    # ---- What-if Scenarios ----
    st.sidebar.markdown("---")
    st.sidebar.markdown("### What-if Scenarios")
    st.sidebar.caption(
        "Adjusts the city scores — what if real-world conditions changed? "
        "**See how cities hold up when conditions worsen. Toggle one or more scenarios.**"
    )

    drought_mode = st.sidebar.checkbox(
        "🌵 Drought Year",
        value=False,
        key="scn_drought",
        help=(
            "Sustained dry conditions (~20–25% less water available). "
            "Calibrated to U.S. Drought Monitor 'D2 Severe' classification "
            "(2011 Texas, 2012–2016 California). Lowers Baseline Water Stress "
            "and Annual Precipitation by 25%, Water & Sewer Cost by 20%, "
            "Cooling Degree Days by 15%, Renewable Energy Mix by 10% (hydropower drop)."
        ),
    )
    flood_mode = st.sidebar.checkbox(
        "🌊 Major Flood Event",
        value=False,
        key="scn_flood",
        help=(
            "100-year flood, hurricane storm surge, or major river flood. "
            "Calibrated to Hurricane Harvey (Houston 2017, $125B damages, "
            "40% of wastewater plants offline). Lowers Flood Risk by 30%, "
            "Recycled Water Infrastructure by 20%, Industrial Electricity "
            "Rate by 15%, Environmental Justice Index by 15%, Tornado Frequency by 10%."
        ),
    )
    wildfire_mode = st.sidebar.checkbox(
        "🔥 Wildfire Season",
        value=False,
        key="scn_wildfire",
        help=(
            "Extended period of active wildfires. Calibrated to California 2020 "
            "(4M+ acres burned, solar output dropped ~30% during peak smoke). "
            "Lowers Wildfire Hazard by 25%, Annual Mean Humidity by 15%, "
            "Renewable Energy Mix by 20%, Industrial Electricity Rate by 10%."
        ),
    )
    tech_boom_mode = st.sidebar.checkbox(
        "💼 Tech Industry Boom",
        value=False,
        key="scn_tech_boom",
        help=(
            "Rapid data-center cluster growth competes for local resources. "
            "Calibrated to Loudoun County VA, Dublin Ireland (2022 grid moratorium), "
            "and Phoenix 2023 groundwater rules. Lowers Industrial Electricity "
            "Rate by 20%, Baseline Water Stress by 15%, Environmental Justice "
            "Index and Water & Sewer Cost by 15%. BONUS: Recycled Water "
            "Infrastructure +10% (reuse capacity becomes more valuable under competition)."
        ),
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("DCS Dashboard · Scale 1–5 (5 = best for siting)")

    scenario_flags = {
        "drought":   drought_mode,
        "flood":     flood_mode,
        "wildfire":  wildfire_mode,
        "tech_boom": tech_boom_mode,
    }
    return active_weights, scenario_name, scenario_flags


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_starting_weights(
    scenario_name: str,
    workbook_default_weights: Optional[Dict[str, float]],
) -> Dict[str, float]:
    """Return the weight dict the sliders should display for this scenario."""
    if scenario_name != CUSTOM_MODE_NAME:
        return SCENARIO_WEIGHTS[scenario_name]

    # Custom mode — restore last applied custom values, else fall back.
    committed = st.session_state.get("_custom_committed")
    if committed and all(c in committed for c in CATEGORIES):
        return committed
    if (
        workbook_default_weights
        and all(c in workbook_default_weights for c in CATEGORIES)
    ):
        return workbook_default_weights
    return DEFAULT_WEIGHTS.copy()


def _sync_slider_state(
    scenario_name: str,
    target_weights: Dict[str, float],
) -> None:
    """
    On scenario change, write target_weights into the slider session-state
    keys so the sliders display the correct values for the new mode.

    This is safe to call BEFORE the sliders are rendered — Streamlit only
    forbids writing to widget state AFTER the widget has been instantiated.
    """
    last = st.session_state.get("_last_decision_mode")
    if last == scenario_name:
        return
    st.session_state["_last_decision_mode"] = scenario_name
    for cat in CATEGORIES:
        st.session_state[f"weight_slider_{cat}"] = float(round(target_weights[cat], 2))
    # Seed the committed bucket the first time we enter Custom Weights.
    if scenario_name == CUSTOM_MODE_NAME and "_custom_committed" not in st.session_state:
        st.session_state["_custom_committed"] = dict(target_weights)


def _render_custom_apply_controls(
    draft_weights: Dict[str, float],
) -> Dict[str, float]:
    """
    Render the running-sum indicator and Apply / Reset buttons. Returns
    the weights currently committed to the rankings (i.e. the values
    the user last applied — NOT the unapplied draft).
    """
    draft_total = sum(draft_weights.values())
    remaining = 1.0 - draft_total
    is_valid_sum = abs(remaining) <= _SUM_TOLERANCE

    committed = st.session_state.get("_custom_committed", DEFAULT_WEIGHTS.copy())
    has_drift = any(
        abs(draft_weights[cat] - committed.get(cat, 0.0)) > _SUM_TOLERANCE
        for cat in CATEGORIES
    )

    # Live budget indicator
    if is_valid_sum and not has_drift:
        st.sidebar.success("✓ Weights applied (Total: **1.00**)")
    elif is_valid_sum and has_drift:
        st.sidebar.success(
            "✓ Total: **1.00** — click **Apply Weights** to use these values."
        )
    elif draft_total < 1.0:
        st.sidebar.warning(
            f"Total: **{draft_total:.2f}**  ·  Remaining: **+{remaining:.2f}**"
        )
    else:
        st.sidebar.error(
            f"Total: **{draft_total:.2f}**  ·  Over by **{-remaining:.2f}**"
        )

    # Apply button: enabled only when sum is valid AND there's something to apply.
    st.sidebar.button(
        "✅ Apply Weights",
        on_click=_apply_weights_callback,
        disabled=not (is_valid_sum and has_drift),
        use_container_width=True,
        help="Commit these weights to the rankings.",
    )

    # Reset to app defaults
    st.sidebar.button(
        "↺ Reset to defaults",
        on_click=_reset_to_defaults_callback,
        use_container_width=True,
        help="Reset sliders to 25 / 30 / 15 / 20 / 10.",
    )

    return dict(committed)
