"""
scenarios.py – Scenario toggles for Siteworks.

Provides weight presets and score modifiers for the "what-if" scenarios
described in the project roadmap and slide deck.  Each scenario either
  (a) adjusts the category weights, or
  (b) applies multipliers to subcategory scores to simulate different
      operating conditions.

All scenarios are clearly labelled as prototype placeholders where
the underlying data is incomplete.
"""

from typing import Dict, Optional

from src.data.schema import DEFAULT_WEIGHTS, CATEGORIES, CityData

# ---------------------------------------------------------------------------
# Named weight presets
# ---------------------------------------------------------------------------

SCENARIO_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Default": DEFAULT_WEIGHTS.copy(),
    "Water Stress Emphasis": {
        "Hydrological & Regulatory Risk": 0.40,
        "Climate & Operational Physics":  0.25,
        "Economic & Social Impact":       0.10,
        "Natural Hazards":                0.15,
        "Biodiversity":                   0.10,
    },
    "Carbon / Grid Emphasis": {
        "Hydrological & Regulatory Risk": 0.15,
        "Climate & Operational Physics":  0.45,
        "Economic & Social Impact":       0.15,
        "Natural Hazards":                0.15,
        "Biodiversity":                   0.10,
    },
    "Cost Optimisation": {
        "Hydrological & Regulatory Risk": 0.20,
        "Climate & Operational Physics":  0.20,
        "Economic & Social Impact":       0.35,
        "Natural Hazards":                0.15,
        "Biodiversity":                   0.10,
    },
    "Hazard Minimisation": {
        "Hydrological & Regulatory Risk": 0.20,
        "Climate & Operational Physics":  0.20,
        "Economic & Social Impact":       0.10,
        "Natural Hazards":                0.40,
        "Biodiversity":                   0.10,
    },
}

SCENARIO_DESCRIPTIONS: Dict[str, str] = {
    "Default": "Balanced weighting across all five sustainability categories.",
    "Water Stress Emphasis": (
        "Heavily weights water availability and regulatory risk. "
        "Best for regions facing near-term drought or groundwater depletion."
    ),
    "Carbon / Grid Emphasis": (
        "Prioritises grid cleanliness and renewable energy mix. "
        "Useful for organisations with net-zero commitments."
    ),
    "Cost Optimisation": (
        "Maximises weight on economic factors (electricity rates, water costs). "
        "Use when capital budget is the primary constraint."
    ),
    "Hazard Minimisation": (
        "Focuses on physical risk reduction – floods, tornadoes, and weather. "
        "Appropriate for critical infrastructure with high uptime requirements."
    ),
}

# ---------------------------------------------------------------------------
# Score modifiers (prototype – requires richer dataset to fully implement)
# ---------------------------------------------------------------------------

def apply_drought_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    [PROTOTYPE PLACEHOLDER] Simulate a drought year by reducing water-related
    scores.  Currently applies a fixed 20% penalty to Baseline Water Stress
    and Annual Precipitation scores.

    Requires future climate projection data to implement fully.
    """
    import copy
    import math
    adjusted = copy.deepcopy(city_data)
    affected_subs = ["Baseline Water Stress", "Annual Precipitation"]
    for cd in adjusted.values():
        for sub in affected_subs:
            entry = cd.subcategory_scores.get(sub)
            if entry and not math.isnan(entry.score):
                entry.score = max(1.0, round(entry.score * 0.80, 2))
                entry.note = (entry.note or "") + " [Drought scenario: –20%]"
    return adjusted


def apply_future_climate_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    [PROTOTYPE PLACEHOLDER] 2050 climate shift scenario.

    Applies projected changes:
    • Cooling Degree Days: +10% (more cooling needed)
    • Baseline Water Stress: –15% (increased stress)
    • Flood Risk: –10% (increasing flood probability)

    Data source for full implementation: CMIP6 regional projections.
    """
    import copy
    import math
    adjustments = {
        "Cooling Degree Days":   0.90,  # more CDD → lower score
        "Baseline Water Stress": 0.85,
        "Flood Risk":            0.90,
    }
    adjusted = copy.deepcopy(city_data)
    for cd in adjusted.values():
        for sub, factor in adjustments.items():
            entry = cd.subcategory_scores.get(sub)
            if entry and not math.isnan(entry.score):
                entry.score = max(1.0, round(entry.score * factor, 2))
                entry.note = (entry.note or "") + " [2050 climate scenario]"
    return adjusted
