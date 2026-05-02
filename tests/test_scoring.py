"""
test_scoring.py – Unit tests for the Siteworks scoring engine.
"""

import math
import pytest

from src.data.schema import (
    CATEGORIES,
    DEFAULT_WEIGHTS,
    SUBCATEGORIES,
    CityData,
    SubcategoryScore,
)
from src.logic.scoring import (
    compute_category_score,
    score_city,
    rank_cities,
    normalize_weights,
    reset_to_defaults,
    get_missing_scores,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_city(name: str, score: float) -> CityData:
    """Create a CityData with all subcategories set to `score`."""
    cd = CityData(name=name)
    for cat, subs in SUBCATEGORIES.items():
        for sub in subs:
            cd.subcategory_scores[sub] = SubcategoryScore(name=sub, score=score)
    return cd


def _make_varied_city(name: str, scores: dict) -> CityData:
    """Create a CityData with specific subcategory scores."""
    cd = CityData(name=name)
    for sub, score in scores.items():
        cd.subcategory_scores[sub] = SubcategoryScore(name=sub, score=score)
    return cd


# ---------------------------------------------------------------------------
# compute_category_score
# ---------------------------------------------------------------------------

class TestComputeCategoryScore:
    def test_all_scores_same(self):
        cd = _make_city("Test", 4.0)
        avg, missing = compute_category_score(cd, "Hydrological & Regulatory Risk")
        assert avg == pytest.approx(4.0)
        assert missing == []

    def test_missing_subcategory(self):
        cd = CityData(name="Sparse")
        # Provide only some subcategories
        cat = "Hydrological & Regulatory Risk"
        subs = SUBCATEGORIES[cat]
        cd.subcategory_scores[subs[0]] = SubcategoryScore(name=subs[0], score=3.0)
        avg, missing = compute_category_score(cd, cat)
        assert avg == pytest.approx(3.0)
        assert len(missing) == len(subs) - 1

    def test_all_nan_returns_zero(self):
        cd = CityData(name="Empty")
        avg, missing = compute_category_score(cd, "Natural Hazards")
        assert avg == 0.0
        assert len(missing) == len(SUBCATEGORIES["Natural Hazards"])

    def test_nan_score_treated_as_missing(self):
        cd = CityData(name="NaN City")
        cat = "Biodiversity"
        sub = SUBCATEGORIES[cat][0]
        cd.subcategory_scores[sub] = SubcategoryScore(name=sub, score=float("nan"))
        avg, missing = compute_category_score(cd, cat)
        assert avg == 0.0
        assert sub in missing


# ---------------------------------------------------------------------------
# score_city
# ---------------------------------------------------------------------------

class TestScoreCity:
    def test_uniform_scores_weighted_total(self):
        cd = _make_city("Uniform", 3.0)
        result = score_city(cd)
        # With all category scores = 3.0 and weights summing to 1, total = 3.0
        assert result.total_score == pytest.approx(3.0, abs=1e-3)
        assert result.city == "Uniform"

    def test_custom_weights_change_total(self):
        cd = _make_city("Test", 3.0)
        custom_weights = {cat: 0.2 for cat in CATEGORIES}
        result = score_city(cd, weights=custom_weights)
        assert result.total_score == pytest.approx(3.0, abs=1e-3)

    def test_score_in_range(self):
        cd = _make_city("InRange", 4.5)
        result = score_city(cd)
        assert 1.0 <= result.total_score <= 5.0

    def test_uses_default_weights_when_none(self):
        cd = _make_city("Default", 2.0)
        result = score_city(cd)
        assert result.weights_used == DEFAULT_WEIGHTS


# ---------------------------------------------------------------------------
# rank_cities
# ---------------------------------------------------------------------------

class TestRankCities:
    def _make_dataset(self):
        return {
            "Alpha": _make_city("Alpha", 5.0),
            "Beta":  _make_city("Beta",  3.0),
            "Gamma": _make_city("Gamma", 1.0),
        }

    def test_ranking_order(self):
        data = self._make_dataset()
        results = rank_cities(data)
        assert [r.city for r in results] == ["Alpha", "Beta", "Gamma"]

    def test_ranks_assigned(self):
        data = self._make_dataset()
        results = rank_cities(data)
        assert results[0].rank == 1
        assert results[-1].rank == len(results)

    def test_rank_count_matches_cities(self):
        data = self._make_dataset()
        results = rank_cities(data)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# normalize_weights
# ---------------------------------------------------------------------------

class TestNormalizeWeights:
    def test_already_normalized(self):
        raw = {cat: DEFAULT_WEIGHTS[cat] for cat in CATEGORIES}
        norm = normalize_weights(raw)
        assert abs(sum(norm.values()) - 1.0) < 1e-6

    def test_unnormalized_input(self):
        raw = {cat: 1.0 for cat in CATEGORIES}  # sum = 5.0
        norm = normalize_weights(raw)
        assert abs(sum(norm.values()) - 1.0) < 1e-6
        for cat in CATEGORIES:
            assert norm[cat] == pytest.approx(0.2, abs=1e-4)

    def test_all_zero_raises(self):
        raw = {cat: 0.0 for cat in CATEGORIES}
        with pytest.raises(ValueError, match="zero"):
            normalize_weights(raw)

    def test_negative_clamped_to_zero(self):
        raw = {cat: -1.0 for cat in CATEGORIES}
        raw[CATEGORIES[0]] = 1.0
        norm = normalize_weights(raw)
        assert norm[CATEGORIES[0]] == pytest.approx(1.0)
        for cat in CATEGORIES[1:]:
            assert norm[cat] == pytest.approx(0.0)

    def test_sum_always_one(self):
        import random
        random.seed(42)
        for _ in range(10):
            raw = {cat: random.random() for cat in CATEGORIES}
            norm = normalize_weights(raw)
            assert abs(sum(norm.values()) - 1.0) < 1e-5


# ---------------------------------------------------------------------------
# reset_to_defaults
# ---------------------------------------------------------------------------

class TestResetToDefaults:
    def test_returns_default_weights(self):
        result = reset_to_defaults()
        assert result == DEFAULT_WEIGHTS

    def test_returns_copy(self):
        result = reset_to_defaults()
        result["Biodiversity"] = 0.99
        assert DEFAULT_WEIGHTS["Biodiversity"] == 0.10


# ---------------------------------------------------------------------------
# get_missing_scores
# ---------------------------------------------------------------------------

class TestGetMissingScores:
    def test_no_missing(self):
        data = {"A": _make_city("A", 3.0)}
        missing = get_missing_scores(data)
        assert missing == {}

    def test_detects_missing(self):
        cd = CityData(name="Sparse")
        data = {"Sparse": cd}
        missing = get_missing_scores(data)
        assert "Sparse" in missing
        assert len(missing["Sparse"]) > 0
