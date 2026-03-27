"""
schema.py – Normalized data model for Siteworks.

All scoring data is stored in Python dataclasses / dicts using this schema.
If the Excel workbook is present, the parser maps its raw cells into these
structures.  If not, the loader falls back to the built-in pilot dataset.

Score convention:  1 (worst) … 5 (best) for every subcategory.
Higher is always "better for siting a data center."
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Category and weight definitions
# ---------------------------------------------------------------------------

CATEGORIES: List[str] = [
    "Hydrological & Regulatory Risk",
    "Climate & Operational Physics",
    "Economic & Social Impact",
    "Natural Hazards",
    "Biodiversity",
]

DEFAULT_WEIGHTS: Dict[str, float] = {
    "Hydrological & Regulatory Risk": 0.25,
    "Climate & Operational Physics":  0.30,
    "Economic & Social Impact":       0.15,
    "Natural Hazards":                0.20,
    "Biodiversity":                   0.10,
}

# Subcategories grouped by their parent category
SUBCATEGORIES: Dict[str, List[str]] = {
    "Hydrological & Regulatory Risk": [
        "Baseline Water Stress",
        "Annual Precipitation",
        "Recycled Water Infrastructure",
    ],
    "Climate & Operational Physics": [
        "Cooling Degree Days",
        "Annual Mean Humidity",
        "Grid Carbon Intensity",
        "Renewable Energy Mix",
    ],
    "Economic & Social Impact": [
        "Industrial Electricity Rate",
        "Water & Sewer Cost",
        "Environmental Justice Index",
    ],
    "Natural Hazards": [
        "Flood Risk",
        "Tornado Frequency",
        "Wildlife Hazard",
        "Winter Weather Disruption",
    ],
    "Biodiversity": [
        "Protected Area Proximity",
    ],
}

# Plain-language tooltips shown to non-engineer users
SUBCATEGORY_TOOLTIPS: Dict[str, str] = {
    "Baseline Water Stress":          "How scarce is water in this region? (lower stress = better score)",
    "Annual Precipitation":           "How much rainfall replenishes local water supplies each year?",
    "Recycled Water Infrastructure":  "Is there existing grey-water / recycled-water infrastructure?",
    "Cooling Degree Days":            "How many days require active cooling? Fewer = lower energy cost.",
    "Annual Mean Humidity":           "High humidity raises cooling load and equipment risk.",
    "Grid Carbon Intensity":          "How clean is the local electrical grid? (lower carbon = better)",
    "Renewable Energy Mix":           "Share of renewables in the local grid.",
    "Industrial Electricity Rate":    "Cost of electricity for large industrial consumers.",
    "Water & Sewer Cost":             "Cost of water procurement and wastewater disposal.",
    "Environmental Justice Index":    "Community equity and regulatory / reputational risk.",
    "Flood Risk":                     "Probability and severity of flooding events.",
    "Tornado Frequency":              "Historical tornado activity in the region.",
    "Wildlife Hazard":                "Risk of wildlife-related disruptions (e.g., bird strikes, pests).",
    "Winter Weather Disruption":      "Likelihood of ice/snow events disrupting operations.",
    "Protected Area Proximity":       "Proximity to protected lands – closer may limit expansion.",
}

# Source URLs where available (populated from workbook; kept here as reference)
SUBCATEGORY_SOURCES: Dict[str, str] = {
    "Baseline Water Stress":          "https://www.wri.org/data/aqueduct-water-risk-atlas",
    "Annual Precipitation":           "https://www.ncei.noaa.gov/",
    "Recycled Water Infrastructure":  "https://www.waterreuse.org/",
    "Cooling Degree Days":            "https://www.eia.gov/",
    "Annual Mean Humidity":           "https://www.ncei.noaa.gov/",
    "Grid Carbon Intensity":          "https://www.epa.gov/egrid",
    "Renewable Energy Mix":           "https://www.eia.gov/",
    "Industrial Electricity Rate":    "https://www.eia.gov/electricity/",
    "Water & Sewer Cost":             "https://www.awwa.org/",
    "Environmental Justice Index":    "https://ejscreen.epa.gov/",
    "Flood Risk":                     "https://msc.fema.gov/portal/home",
    "Tornado Frequency":              "https://www.spc.noaa.gov/",
    "Wildlife Hazard":                "https://www.fws.gov/",
    "Winter Weather Disruption":      "https://www.ncei.noaa.gov/",
    "Protected Area Proximity":       "https://www.protectedplanet.net/",
}

PILOT_CITIES: List[str] = [
    "Oklahoma City",
    "Boston",
    "Denver",
    "Houston",
    "Gainesville",
]


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SubcategoryScore:
    """Score for a single subcategory metric within a city."""
    name: str
    score: float               # 1–5, higher = better
    raw_value: Optional[str] = None   # original measurement (for transparency)
    note: Optional[str] = None


@dataclass
class CityData:
    """All scoring data for one city."""
    name: str
    subcategory_scores: Dict[str, SubcategoryScore] = field(default_factory=dict)
    # category_scores are derived; not stored here – computed by scoring.py
    data_quality_notes: List[str] = field(default_factory=list)

    def get_score(self, subcategory: str) -> Optional[float]:
        """Return score for a subcategory, or None if missing."""
        entry = self.subcategory_scores.get(subcategory)
        return entry.score if entry else None


@dataclass
class ScoringResult:
    """Full scoring output for a single city."""
    city: str
    category_scores: Dict[str, float]   # category → average score
    total_score: float
    rank: int = 0                        # filled in after ranking all cities
    weights_used: Dict[str, float] = field(default_factory=dict)
