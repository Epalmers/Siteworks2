"""
summaries.py – Template-based natural language summary generator.

Produces plain-English explanations of ranking results without calling
any external LLM API.  Text is deterministic and reproducible.
"""

from typing import Dict, List

from src.data.schema import CATEGORIES, ScoringResult


# ---------------------------------------------------------------------------
# Category short labels (used in readable sentences)
# ---------------------------------------------------------------------------

_CAT_LABELS: Dict[str, str] = {
    "Hydrological & Regulatory Risk": "water availability and regulatory risk",
    "Climate & Operational Physics":  "climate and grid performance",
    "Economic & Social Impact":       "economic and cost factors",
    "Natural Hazards":                "natural hazard exposure",
    "Biodiversity":                   "biodiversity constraints",
}

_SCORE_ADJ: List[tuple] = [
    (4.5, "excellent"),
    (3.75, "strong"),
    (3.0, "moderate"),
    (2.25, "below-average"),
    (0.0, "weak"),
]


def _adj(score: float) -> str:
    for threshold, label in _SCORE_ADJ:
        if score >= threshold:
            return label
    return "weak"


def _top_n(scores: Dict[str, float], n: int = 2, best: bool = True) -> List[str]:
    """Return the n best (or worst) category keys by score."""
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=best)
    return [k for k, _ in sorted_cats[:n]]


# ---------------------------------------------------------------------------
# Public summary functions
# ---------------------------------------------------------------------------

def top_city_summary(result: ScoringResult) -> str:
    """One-paragraph summary for the top-ranked city."""
    strengths = _top_n(result.category_scores, n=2, best=True)
    weaknesses = _top_n(result.category_scores, n=1, best=False)

    strength_text = " and ".join(
        f"{_adj(result.category_scores[c])} {_CAT_LABELS.get(c, c)}"
        for c in strengths
    )
    weakness_text = (
        f"{_CAT_LABELS.get(weaknesses[0], weaknesses[0])} "
        f"({_adj(result.category_scores[weaknesses[0]])} score of "
        f"{result.category_scores[weaknesses[0]]:.2f})"
        if weaknesses else "no major weaknesses identified"
    )

    return (
        f"**{result.city}** ranks first with an overall score of "
        f"**{result.total_score:.2f}/5.00**. "
        f"It benefits from {strength_text}. "
        f"The main area of concern is {weakness_text}. "
        f"This profile suggests a good long-term siting prospect, but "
        f"due diligence on the noted weakness is still recommended."
    )


def bottom_city_summary(result: ScoringResult) -> str:
    """One-paragraph summary for the bottom-ranked city."""
    drivers = _top_n(result.category_scores, n=2, best=False)

    driver_text = " and ".join(
        f"{_CAT_LABELS.get(c, c)} ({_adj(result.category_scores[c])})"
        for c in drivers
    )

    return (
        f"**{result.city}** ranks last with an overall score of "
        f"**{result.total_score:.2f}/5.00**. "
        f"The primary factors dragging its score down are {driver_text}. "
        f"Improving performance in these areas—whether through infrastructure "
        f"investment or negotiating water/power agreements—would be necessary "
        f"before this site can compete with higher-ranked alternatives."
    )


def weight_change_note(
    old_top: str,
    new_top: str,
    changed_category: str,
) -> str:
    """Explain why the top city changed after a weight adjustment."""
    if old_top == new_top:
        return (
            f"Adjusting the weight of **{changed_category}** did not change "
            f"the top-ranked city ({old_top}), but relative scores shifted."
        )
    return (
        f"After increasing the weight of **{changed_category}**, "
        f"**{new_top}** moved ahead of {old_top} as the top-ranked city. "
        f"This indicates that {new_top} has a stronger profile in that "
        f"category than {old_top}."
    )


def city_comparison_summary(a: ScoringResult, b: ScoringResult) -> str:
    """Short comparison paragraph for two cities."""
    winner = a if a.total_score >= b.total_score else b
    loser = b if a.total_score >= b.total_score else a
    diff = abs(a.total_score - b.total_score)

    better_cats = [
        c for c in CATEGORIES
        if a.category_scores.get(c, 0) > b.category_scores.get(c, 0)
    ]
    a_leads = ", ".join(
        _CAT_LABELS.get(c, c) for c in better_cats[:2]
    ) or "no clear categories"

    b_leads_cats = [
        c for c in CATEGORIES
        if b.category_scores.get(c, 0) > a.category_scores.get(c, 0)
    ]
    b_leads = ", ".join(
        _CAT_LABELS.get(c, c) for c in b_leads_cats[:2]
    ) or "no clear categories"

    gap_desc = "slightly" if diff < 0.2 else "notably" if diff < 0.5 else "significantly"

    return (
        f"**{winner.city}** outscores **{loser.city}** by **{diff:.2f} points** "
        f"({gap_desc}). "
        f"{a.city} leads on {a_leads}. "
        f"{b.city} leads on {b_leads}. "
        f"The best choice between these two depends on which factors matter "
        f"most for your organisation's priorities."
    )


def scenario_summary(scenario_name: str, results: List[ScoringResult]) -> str:
    """Brief note about the current scenario and top result."""
    top = results[0]
    return (
        f"Under the **{scenario_name}** scenario, **{top.city}** scores highest "
        f"({top.total_score:.2f}/5.00). "
        f"Use the weight sliders or scenario presets to explore how the "
        f"ranking changes under different priorities."
    )
