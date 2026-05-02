"""
scoring.py – Weighted MCDA scoring engine for Siteworks.

Algorithm (from CIVE580 Algorithms for AI.docx):
    1. For each city, compute category score = average of its subcategory scores.
    2. Total Score = Σ (category_score × weight) for all 5 categories.
    3. Rank cities from highest total score (best) to lowest.

Missing subcategory scores are excluded from the category average
rather than treated as zero, to avoid penalising cities with sparse data.
A warning is surfaced in the UI when scores are missing.
"""

import math
from typing import Dict, List, Optional, Tuple

from src.data.schema import (
    CATEGORIES,
    DEFAULT_WEIGHTS,
    SUBCATEGORIES,
    CityData,
    ScoringResult,
)


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def compute_category_score(
    city: CityData,
    category: str,
) -> Tuple[float, List[str]]:
    """
    Return (average_score, missing_subcategories) for one city+category.

    Missing subcategories are those whose score is NaN or absent.
    """
    subs = SUBCATEGORIES.get(category, [])
    scores = []
    missing = []
    for sub in subs:
        entry = city.subcategory_scores.get(sub)
        if entry is None or math.isnan(entry.score):
            missing.append(sub)
        else:
            scores.append(entry.score)

    avg = sum(scores) / len(scores) if scores else 0.0
    return avg, missing


def score_city(
    city: CityData,
    weights: Optional[Dict[str, float]] = None,
) -> ScoringResult:
    """
    Compute the full weighted score for a single city.

    Parameters:
        city    : CityData object for the city.
        weights : category → weight mapping (must sum to 1.0).
                  Defaults to DEFAULT_WEIGHTS.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    category_scores: Dict[str, float] = {}
    for cat in CATEGORIES:
        avg, _ = compute_category_score(city, cat)
        category_scores[cat] = avg

    total = sum(
        category_scores[cat] * weights.get(cat, 0.0)
        for cat in CATEGORIES
    )

    return ScoringResult(
        city=city.name,
        category_scores=category_scores,
        total_score=round(total, 4),
        weights_used=weights.copy(),
    )


def rank_cities(
    city_data: Dict[str, CityData],
    weights: Optional[Dict[str, float]] = None,
) -> List[ScoringResult]:
    """
    Score and rank all cities.  Returns list sorted best→worst.
    """
    results = [score_city(cd, weights) for cd in city_data.values()]
    results.sort(key=lambda r: r.total_score, reverse=True)
    for idx, result in enumerate(results, start=1):
        result.rank = idx
    return results


# ---------------------------------------------------------------------------
# Weight utilities
# ---------------------------------------------------------------------------

def normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    """
    Normalise a weight mapping so values sum to exactly 1.0.

    Any category with a negative raw value is clamped to 0.
    Raises ValueError if all weights are zero.
    """
    clamped = {k: max(0.0, v) for k, v in raw.items()}
    total = sum(clamped.values())
    if total == 0:
        raise ValueError("All weights are zero – cannot normalise.")
    return {k: round(v / total, 6) for k, v in clamped.items()}


def reset_to_defaults() -> Dict[str, float]:
    """Return a fresh copy of the default weight mapping."""
    return DEFAULT_WEIGHTS.copy()


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def get_missing_scores(city_data: Dict[str, CityData]) -> Dict[str, List[str]]:
    """Return city → [missing subcategory names] for all cities."""
    result: Dict[str, List[str]] = {}
    for city_name, cd in city_data.items():
        missing = []
        for cat in CATEGORIES:
            _, miss = compute_category_score(cd, cat)
            missing.extend(miss)
        if missing:
            result[city_name] = missing
    return result
