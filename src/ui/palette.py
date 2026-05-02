"""
Okabe–Ito color palette for color-vision–accessible data graphics.

Reference: Okabe & Ito, "Color Universal Design (CUD) — How to make figures and
presentations that are friendly to Colorblind people" (Tokyo, 2008).

Hex values use the standard CUD set (the infographic the user provided duplicated
hex labels for blue/yellow; we use the canonical values #0072B2 and #F0E442).
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Named swatches (Okabe–Ito)
# ---------------------------------------------------------------------------

OKABE_ITO_ORANGE = "#E69F00"
OKABE_ITO_SKY_BLUE = "#56B4E9"
OKABE_ITO_BLUISH_GREEN = "#009E73"
OKABE_ITO_YELLOW = "#F0E442"
OKABE_ITO_BLUE = "#0072B2"
OKABE_ITO_VERMILION = "#D55E00"
OKABE_ITO_REDDISH_PURPLE = "#CC79A7"
OKABE_ITO_BLACK = "#000000"

# ---------------------------------------------------------------------------
# Sequential score ramp (1 = lowest … 5 = highest on the app’s 1–5 scale)
# Uses distinguishable hues; progression reads “cooler / safer” toward green–blue.
# ---------------------------------------------------------------------------

SCORE_COLORS_LOW_TO_HIGH: Tuple[str, ...] = (
    OKABE_ITO_VERMILION,
    OKABE_ITO_ORANGE,
    OKABE_ITO_YELLOW,
    OKABE_ITO_SKY_BLUE,
    OKABE_ITO_BLUISH_GREEN,
)

PLOTLY_SCORE_COLORSCALE: List[List[float | str]] = [
    [0.0, SCORE_COLORS_LOW_TO_HIGH[0]],
    [0.25, SCORE_COLORS_LOW_TO_HIGH[1]],
    [0.5, SCORE_COLORS_LOW_TO_HIGH[2]],
    [0.75, SCORE_COLORS_LOW_TO_HIGH[3]],
    [1.0, SCORE_COLORS_LOW_TO_HIGH[4]],
]

# Matplotlib / pandas Styler background_gradient
TABLE_SCORE_CMAP_COLORS: List[str] = list(SCORE_COLORS_LOW_TO_HIGH)

# ---------------------------------------------------------------------------
# Discrete city colors (one hue per pilot city; fallback cycles unused Okabe hues)
# ---------------------------------------------------------------------------

CITY_COLORS: Dict[str, str] = {
    "Denver": OKABE_ITO_BLUISH_GREEN,
    "Oklahoma City": OKABE_ITO_BLUE,
    "Boston": OKABE_ITO_REDDISH_PURPLE,
    "Gainesville": OKABE_ITO_ORANGE,
    "Houston": OKABE_ITO_VERMILION,
}

_CYCLE_UNKNOWN: Tuple[str, ...] = (
    OKABE_ITO_SKY_BLUE,
    OKABE_ITO_YELLOW,
    OKABE_ITO_ORANGE,
    OKABE_ITO_REDDISH_PURPLE,
    OKABE_ITO_BLUE,
    OKABE_ITO_BLUISH_GREEN,
    OKABE_ITO_VERMILION,
)


def city_color(city: str) -> str:
    """Canonical fill/stroke color for a city in charts and maps."""
    if city in CITY_COLORS:
        return CITY_COLORS[city]
    digest = hashlib.md5(city.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_CYCLE_UNKNOWN)
    return _CYCLE_UNKNOWN[idx]


def score_colour(score: float, min_s: float = 1.0, max_s: float = 5.0) -> str:
    """Map a numeric score to a hex color along the Okabe–Ito score ramp."""
    norm = max(0.0, min(1.0, (score - min_s) / (max_s - min_s)))
    stops = list(zip([0.0, 0.25, 0.5, 0.75, 1.0], SCORE_COLORS_LOW_TO_HIGH))
    for threshold, colour in reversed(stops):
        if norm >= threshold:
            return colour
    return SCORE_COLORS_LOW_TO_HIGH[0]


# Plot chrome (axes, reference lines) — neutral but paired with Okabe black where emphasis helps
CHART_ANNOTATION = OKABE_ITO_BLACK
CHART_GRID = "#CBD5E1"
CHART_REFERENCE_LINE = OKABE_ITO_BLACK
