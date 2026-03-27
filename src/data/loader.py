"""
loader.py – Data loader for Siteworks.

Tries to load from the RH workbook first; falls back to the built-in pilot
dataset if the file is absent or unreadable.

Built-in scores are sourced from the 'Data_Center_Site_Selector_RH.xlsx'
workbook interpretation described in the project documentation.  Where exact
workbook values were not available, scores were estimated from publicly
available data (NOAA, EIA, WRI Aqueduct, FEMA, NOAA Storm Prediction Center)
and are documented in DATA_QUALITY_NOTES.  All scores use a 1–5 scale
where 5 = most favourable for data-center siting.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.data.schema import (
    SUBCATEGORIES,
    SubcategoryScore,
    CityData,
)
from src.data.parser import parse_rh_workbook

# Path where the RH workbook is expected
_WORKBOOK_PATH = Path(__file__).parent.parent.parent / "data" / "Data_Center_Site_Selector_RH.xlsx"

# ---------------------------------------------------------------------------
# Built-in pilot dataset
# ---------------------------------------------------------------------------
# Scores: 1=worst, 5=best for data-center siting.
# Raw-value strings are representative real-world measurements.
#
# Key assumptions / known limitations:
# • Tornado Frequency for OKC is scored low (1) reflecting tornado alley risk.
# • Cooling Degree Days scored inversely (higher CDD → lower score).
# • Humidity scored inversely (higher humidity → lower score).
# • Grid Carbon Intensity scored inversely (higher carbon → lower score).
# • Flood Risk scored inversely (higher risk → lower score).
# • Protected Area Proximity: closer = more constraint = lower score.
# ---------------------------------------------------------------------------

_PILOT_DATA: Dict[str, Dict[str, Tuple[float, str]]] = {
    # city → subcategory → (score 1-5, raw_value_string)
    "Oklahoma City": {
        "Baseline Water Stress":          (2.5, "Medium-High (WRI Aqueduct)"),
        "Annual Precipitation":           (3.0, "~36 in/yr"),
        "Recycled Water Infrastructure":  (2.0, "Limited programme"),
        "Cooling Degree Days":            (2.5, "~2,700 CDD/yr"),
        "Annual Mean Humidity":           (3.0, "~60% RH"),
        "Grid Carbon Intensity":          (2.5, "~610 lbs CO₂/MWh (SPP)"),
        "Renewable Energy Mix":           (3.5, "~35% (wind-heavy)"),
        "Industrial Electricity Rate":    (5.0, "~$0.054/kWh (low)"),
        "Water & Sewer Cost":             (4.0, "~$3.50/1,000 gal"),
        "Environmental Justice Index":    (3.0, "Moderate EJ concerns"),
        "Flood Risk":                     (3.0, "Moderate (FEMA Zone AE areas)"),
        "Tornado Frequency":              (1.0, "High – Tornado Alley (~60/yr in OK)"),
        "Wildlife Hazard":                (4.0, "Low concern"),
        "Winter Weather Disruption":      (3.0, "Occasional ice storms"),
        "Protected Area Proximity":       (4.0, "Few nearby protected areas"),
    },
    "Boston": {
        "Baseline Water Stress":          (4.0, "Low (WRI Aqueduct)"),
        "Annual Precipitation":           (5.0, "~47 in/yr"),
        "Recycled Water Infrastructure":  (2.5, "Limited recycled-water programme"),
        "Cooling Degree Days":            (4.5, "~800 CDD/yr (low cooling need)"),
        "Annual Mean Humidity":           (2.5, "~70% RH (humid continental)"),
        "Grid Carbon Intensity":          (3.5, "~430 lbs CO₂/MWh (ISO-NE)"),
        "Renewable Energy Mix":           (4.0, "~35% (offshore wind growing)"),
        "Industrial Electricity Rate":    (1.5, "~$0.135/kWh (high)"),
        "Water & Sewer Cost":             (2.5, "~$9.00/1,000 gal (high)"),
        "Environmental Justice Index":    (4.0, "Good EJ policies"),
        "Flood Risk":                     (3.5, "Low-Moderate (coastal, managed)"),
        "Tornado Frequency":              (4.5, "Rare (<1/yr)"),
        "Wildlife Hazard":                (4.0, "Low concern"),
        "Winter Weather Disruption":      (2.0, "Significant snowfall / ice risk"),
        "Protected Area Proximity":       (3.0, "Several protected areas nearby"),
    },
    "Denver": {
        "Baseline Water Stress":          (2.0, "High (semi-arid, WRI Aqueduct)"),
        "Annual Precipitation":           (2.5, "~14 in/yr (semi-arid)"),
        "Recycled Water Infrastructure":  (3.5, "Active recycled-water programmes"),
        "Cooling Degree Days":            (4.0, "~700 CDD/yr (high altitude helps)"),
        "Annual Mean Humidity":           (4.5, "~45% RH (dry climate)"),
        "Grid Carbon Intensity":          (3.0, "~540 lbs CO₂/MWh (WECC-CO)"),
        "Renewable Energy Mix":           (4.0, "~38% (wind + solar)"),
        "Industrial Electricity Rate":    (3.5, "~$0.072/kWh (moderate)"),
        "Water & Sewer Cost":             (3.0, "~$6.00/1,000 gal"),
        "Environmental Justice Index":    (3.5, "Moderate-Good"),
        "Flood Risk":                     (4.0, "Low (mountain runoff managed)"),
        "Tornado Frequency":              (3.5, "Low-Moderate (~10/yr in CO)"),
        "Wildlife Hazard":                (3.5, "Moderate (suburban edge)"),
        "Winter Weather Disruption":      (2.5, "Snowstorms; well-managed roads"),
        "Protected Area Proximity":       (2.0, "Many Rocky Mtn protected areas nearby"),
    },
    "Houston": {
        "Baseline Water Stress":          (3.0, "Medium (WRI Aqueduct)"),
        "Annual Precipitation":           (4.5, "~50 in/yr"),
        "Recycled Water Infrastructure":  (2.0, "Limited recycled programme"),
        "Cooling Degree Days":            (1.5, "~3,200 CDD/yr (very hot/humid)"),
        "Annual Mean Humidity":           (1.5, "~75% RH (very humid)"),
        "Grid Carbon Intensity":          (2.0, "~780 lbs CO₂/MWh (ERCOT)"),
        "Renewable Energy Mix":           (2.5, "~25% (wind growing)"),
        "Industrial Electricity Rate":    (4.0, "~$0.062/kWh (low-moderate)"),
        "Water & Sewer Cost":             (4.0, "~$3.00/1,000 gal"),
        "Environmental Justice Index":    (2.0, "Significant EJ concerns"),
        "Flood Risk":                     (1.0, "Very High (Harvey-type events)"),
        "Tornado Frequency":              (2.5, "Moderate (~25/yr in SE TX)"),
        "Wildlife Hazard":                (3.0, "Moderate (urban wildlife)"),
        "Winter Weather Disruption":      (4.5, "Rare freeze events (URI 2021 noted)"),
        "Protected Area Proximity":       (4.0, "Few protected areas in metro"),
    },
    "Gainesville": {
        "Baseline Water Stress":          (4.5, "Low (Floridan Aquifer system)"),
        "Annual Precipitation":           (5.0, "~52 in/yr"),
        "Recycled Water Infrastructure":  (3.0, "GRU reclaimed water programme"),
        "Cooling Degree Days":            (2.0, "~2,900 CDD/yr (hot & humid)"),
        "Annual Mean Humidity":           (1.5, "~75% RH (subtropical)"),
        "Grid Carbon Intensity":          (2.5, "~560 lbs CO₂/MWh (FRCC)"),
        "Renewable Energy Mix":           (2.5, "~25% (solar growing)"),
        "Industrial Electricity Rate":    (3.0, "~$0.085/kWh"),
        "Water & Sewer Cost":             (3.5, "~$4.50/1,000 gal"),
        "Environmental Justice Index":    (3.5, "University town; active policy"),
        "Flood Risk":                     (3.0, "Moderate (inland, karst terrain)"),
        "Tornado Frequency":              (3.0, "Moderate (~20/yr in FL)"),
        "Wildlife Hazard":                (2.0, "High – gopher tortoises, listed species"),
        "Winter Weather Disruption":      (5.0, "Negligible"),
        "Protected Area Proximity":       (2.0, "Paynes Prairie, Ocala NF nearby"),
    },
}

DATA_QUALITY_NOTES: List[str] = [
    "Scores for this release are derived from the Data_Center_Site_Selector_RH.xlsx "
    "workbook interpretation and supplemented with publicly available data (NOAA, EIA, "
    "WRI Aqueduct, FEMA, NOAA SPC) where workbook values were incomplete.",
    "All scores use a 1–5 scale (5 = most favourable for data-center siting).",
    "Cooling Degree Days, Humidity, Grid Carbon Intensity, Flood Risk, and Tornado "
    "Frequency are scored inversely (higher real-world value → lower score).",
    "Protected Area Proximity is scored inversely: being close to protected land "
    "may restrict site development.",
    "If the workbook 'Data_Center_Site_Selector_RH.xlsx' is placed in the /data folder "
    "it will be parsed automatically and these built-in defaults will be replaced.",
    "CIVE 580 Project MAA.xlsx is a future-expansion template; it is not parsed.",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_city_data() -> Tuple[Dict[str, CityData], List[str], bool]:
    """
    Load city scoring data.

    Returns:
        (city_data_map, quality_notes, from_workbook)
        - city_data_map: city_name → CityData
        - quality_notes: list of data-quality / assumption strings
        - from_workbook: True if loaded from the Excel file, False if built-in
    """
    parsed = parse_rh_workbook(_WORKBOOK_PATH)
    if parsed and len(parsed) >= 3:
        notes = _collect_quality_notes(parsed)
        notes.insert(0, f"✅ Loaded from workbook: {_WORKBOOK_PATH.name}")
        return parsed, notes, True

    city_data = _build_from_pilot()
    return city_data, DATA_QUALITY_NOTES.copy(), False


def _build_from_pilot() -> Dict[str, CityData]:
    """Convert the built-in _PILOT_DATA dict into CityData objects."""
    result: Dict[str, CityData] = {}
    for city_name, sub_scores in _PILOT_DATA.items():
        cd = CityData(name=city_name)
        for sub_name, (score, raw_val) in sub_scores.items():
            cd.subcategory_scores[sub_name] = SubcategoryScore(
                name=sub_name,
                score=score,
                raw_value=raw_val,
                note="Built-in pilot data",
            )
        result[city_name] = cd
    return result


def _collect_quality_notes(city_data: Dict[str, CityData]) -> List[str]:
    """Aggregate data quality notes from parsed city data."""
    notes: List[str] = []
    for city, cd in city_data.items():
        for note in cd.data_quality_notes:
            notes.append(f"{city}: {note}")
    if not notes:
        notes.append("No data quality issues detected in workbook.")
    return notes
