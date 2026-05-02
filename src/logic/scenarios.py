"""
scenarios.py – Decision-mode presets and what-if scenario modifiers.

This file does two things:
  1. Defines the named **Decision Modes** (weight presets) shown in the sidebar.
     Only "Custom Weights" lets the user edit weights; the other four are
     locked recipes designed for specific organisational priorities.
  2. Defines the **What-if Scenarios** — score multipliers that simulate
     real-world disruption events like droughts, floods, wildfires, and
     industry-cluster competition.

All scenario multipliers below are grounded in documented real-world
events and published data, not arbitrary picks. Citations for each
scenario appear in its docstring. They remain *simplified estimates* —
not predictive forecasts — but the magnitudes are calibrated to history.
"""

import copy
import math
from typing import Dict

from src.data.schema import DEFAULT_WEIGHTS, CityData


# ---------------------------------------------------------------------------
# Decision-mode weight presets
# ---------------------------------------------------------------------------
# "Custom Weights" is the ONLY mode that allows the user to edit the
# category weight sliders. The other four lock the sliders to the values
# below — every preset sums to exactly 1.00 by construction.

CUSTOM_MODE_NAME = "Custom Weights"

SCENARIO_WEIGHTS: Dict[str, Dict[str, float]] = {
    CUSTOM_MODE_NAME: DEFAULT_WEIGHTS.copy(),
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
    CUSTOM_MODE_NAME: (
        "Set your own category weights using the sliders below. "
        "The sliders unlock and the weights must sum to **1.00** before "
        "they can be applied to the rankings."
    ),
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
# What-if scenario score modifiers
# ---------------------------------------------------------------------------
# Each scenario applies fixed multiplicative factors to specific subcategory
# scores in a deep-copy of the city data. Most factors are < 1.0 (penalties),
# but some scenarios include "bonus" factors > 1.0 where existing
# infrastructure becomes MORE valuable under stress (e.g. recycled water
# capacity matters more when competition for fresh water intensifies).
#
# Scores are clamped to the [1.0, 5.0] range so results stay inside the
# 1–5 schema convention.

def _apply_modifiers(
    city_data: Dict[str, CityData],
    multipliers: Dict[str, float],
    label: str,
) -> Dict[str, CityData]:
    """Return a deep copy of city_data with per-subcategory multipliers applied."""
    adjusted = copy.deepcopy(city_data)
    for cd in adjusted.values():
        for sub, factor in multipliers.items():
            entry = cd.subcategory_scores.get(sub)
            if entry and not math.isnan(entry.score):
                # Clamp to valid 1-5 score range (allows bonuses up to 5.0).
                new_score = entry.score * factor
                entry.score = max(1.0, min(5.0, round(new_score, 2)))
                entry.note = (entry.note or "") + f" [{label}]"
    return adjusted


def apply_drought_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    Drought Year — sustained dry conditions, ~20-25% less available water.

    Calibrated to the U.S. Drought Monitor's "D2 Severe Drought" classification.
    Real-world references:
      • 2011 Texas drought — reservoirs dropped 30-40%
      • 2012-2016 California drought — water rates rose 15-25%
      • Pacific Northwest 2015 — hydropower output fell 11%

    Affected subcategories:
      • Baseline Water Stress       ×0.75  (less supply, more competition)
      • Annual Precipitation        ×0.75  (rainfall replenishment shortfall)
      • Water & Sewer Cost          ×0.80  (drought rate hikes, 15-25% typical)
      • Cooling Degree Days         ×0.85  (drought years run 1-2°F hotter)
      • Renewable Energy Mix        ×0.90  (hydropower output drops sharply)
    """
    return _apply_modifiers(
        city_data,
        {
            "Baseline Water Stress":  0.75,
            "Annual Precipitation":   0.75,
            "Water & Sewer Cost":     0.80,
            "Cooling Degree Days":    0.85,
            "Renewable Energy Mix":   0.90,
        },
        "Drought Year",
    )


def apply_flood_event_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    Major Flood Event — 100-year flood, hurricane storm surge, or river flood.

    Calibrated to historic major flood events.
    Real-world references:
      • Hurricane Harvey (Houston 2017) — $125B damages, 40% of wastewater
        plants taken offline, 2 weeks of grid disruption
      • Mississippi River 2019 flood — months of industrial disruption
      • Hurricane Ida (Louisiana 2021) — $75B, grid down for 6+ weeks

    Affected subcategories:
      • Flood Risk                       ×0.70  (direct exposure realised)
      • Recycled Water Infrastructure    ×0.80  (treatment plants offline)
      • Industrial Electricity Rate      ×0.85  (grid rebuild costs pass through)
      • Environmental Justice Index      ×0.85  (disproportionate community impact)
      • Tornado Frequency                ×0.90  (hurricane-driven floods spawn tornadoes)
    """
    return _apply_modifiers(
        city_data,
        {
            "Flood Risk":                     0.70,
            "Recycled Water Infrastructure":  0.80,
            "Industrial Electricity Rate":    0.85,
            "Environmental Justice Index":    0.85,
            "Tornado Frequency":              0.90,
        },
        "Major Flood Event",
    )


def apply_wildfire_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    Wildfire Season — extended period of active wildfires in the region.

    Calibrated to severe Western U.S. fire seasons.
    Real-world references:
      • California 2020 — 4M+ acres burned, solar output dropped ~30% during
        peak smoke, public-safety power shutoffs across multiple counties
      • Canadian wildfires 2023 — smoke smothered eastern U.S. for weeks
      • Camp Fire 2018 — caused PG&E grid restructuring and rate hikes

    Note: in this project's schema the **Wildlife Hazard** key actually
    holds *wildfire* hazard data (the workbook column header is "Wildfire
    Hazard"). The schema name is preserved for backward compatibility.

    Affected subcategories:
      • Wildlife Hazard               ×0.75  (active fire risk)
      • Annual Mean Humidity          ×0.85  (extreme dry conditions, smoke)
      • Renewable Energy Mix          ×0.80  (solar curtailed by smoke; CA 2020 saw -30%)
      • Industrial Electricity Rate   ×0.90  (PSPS events and grid rebuild costs)
    """
    return _apply_modifiers(
        city_data,
        {
            "Wildlife Hazard":               0.75,
            "Annual Mean Humidity":          0.85,
            "Renewable Energy Mix":          0.80,
            "Industrial Electricity Rate":   0.90,
        },
        "Wildfire Season",
    )


def apply_tech_boom_scenario(city_data: Dict[str, CityData]) -> Dict[str, CityData]:
    """
    Tech Industry Boom — rapid data-center cluster growth in the region.

    Models market-driven competitive stress rather than a natural disaster.
    Calibrated to documented data-center cluster strain.
    Real-world references:
      • Loudoun County, Virginia — 70%+ of global internet traffic transits
        local data centers; utility rate increases and water-use disputes
      • Dublin, Ireland — 2022 moratorium on new data-center grid connections
        due to ~18% of national electricity demand from existing DCs
      • Phoenix metro 2023 — Arizona's groundwater rules paused new
        large-water-user permits

    Note: this scenario includes a **bonus multiplier** (×1.10) for
    Recycled Water Infrastructure — when freshwater competition tightens,
    cities with strong reuse capacity become MORE attractive, not less.
    This is the opposite of a penalty and demonstrates positional value.

    Affected subcategories:
      • Industrial Electricity Rate    ×0.80  (cluster demand drives rates up)
      • Baseline Water Stress          ×0.85  (other DCs competing for water)
      • Environmental Justice Index    ×0.85  (community pushback on industrial growth)
      • Water & Sewer Cost             ×0.85  (utilities raise rates to expand capacity)
      • Recycled Water Infrastructure  ×1.10  (BONUS – reuse becomes more valuable)
    """
    return _apply_modifiers(
        city_data,
        {
            "Industrial Electricity Rate":    0.80,
            "Baseline Water Stress":          0.85,
            "Environmental Justice Index":    0.85,
            "Water & Sewer Cost":             0.85,
            "Recycled Water Infrastructure":  1.10,
        },
        "Tech Industry Boom",
    )
