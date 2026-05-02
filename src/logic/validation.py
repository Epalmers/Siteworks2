"""
validation.py – Input validation helpers for Siteworks.

Keeps all guard logic in one place so the scoring engine stays clean.
"""

from typing import Dict, List, Tuple

from src.data.schema import CATEGORIES, DEFAULT_WEIGHTS


WEIGHT_TOLERANCE = 1e-4  # acceptable deviation from sum=1.0


def validate_weights(weights: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Check that a weight mapping is valid.

    Returns (is_valid, list_of_issues).
    """
    issues: List[str] = []

    # Check all categories present
    for cat in CATEGORIES:
        if cat not in weights:
            issues.append(f"Missing weight for category: '{cat}'")

    # Check for negatives
    for cat, w in weights.items():
        if w < 0:
            issues.append(f"Negative weight for '{cat}': {w}")

    # Check sum
    total = sum(weights.get(cat, 0.0) for cat in CATEGORIES)
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        issues.append(
            f"Weights sum to {total:.6f} (expected 1.0 ± {WEIGHT_TOLERANCE})"
        )

    return len(issues) == 0, issues


def validate_score_range(score: float, label: str = "Score") -> Tuple[bool, str]:
    """Ensure a score is within [1, 5]."""
    if not (1.0 <= score <= 5.0):
        return False, f"{label} {score:.2f} is outside the expected 1–5 range."
    return True, ""


def weights_sum_to_one(weights: Dict[str, float]) -> bool:
    """Quick boolean check that weights sum to 1 (within tolerance)."""
    return abs(sum(weights.values()) - 1.0) <= WEIGHT_TOLERANCE
