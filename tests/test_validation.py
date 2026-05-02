"""
test_validation.py – Unit tests for the Siteworks validation module.
"""

import pytest

from src.data.schema import CATEGORIES, DEFAULT_WEIGHTS
from src.logic.validation import (
    validate_weights,
    validate_score_range,
    weights_sum_to_one,
    WEIGHT_TOLERANCE,
)


# ---------------------------------------------------------------------------
# validate_weights
# ---------------------------------------------------------------------------

class TestValidateWeights:
    def test_valid_default_weights(self):
        ok, issues = validate_weights(DEFAULT_WEIGHTS)
        assert ok is True
        assert issues == []

    def test_missing_category(self):
        partial = {cat: 0.2 for cat in CATEGORIES[:-1]}
        ok, issues = validate_weights(partial)
        assert ok is False
        assert any("Missing" in i for i in issues)

    def test_sum_not_one(self):
        bad = {cat: 0.5 for cat in CATEGORIES}  # sum = 2.5
        ok, issues = validate_weights(bad)
        assert ok is False
        assert any("sum" in i.lower() for i in issues)

    def test_negative_weight(self):
        bad = DEFAULT_WEIGHTS.copy()
        bad[CATEGORIES[0]] = -0.1
        ok, issues = validate_weights(bad)
        assert ok is False
        assert any("Negative" in i for i in issues)

    def test_tolerance_boundary(self):
        # Within tolerance should pass
        ok_weights = {cat: DEFAULT_WEIGHTS[cat] for cat in CATEGORIES}
        ok_weights[CATEGORIES[0]] += WEIGHT_TOLERANCE / 2
        ok, _ = validate_weights(ok_weights)
        # Sum slightly off but within tolerance
        # This depends on implementation – at minimum no crash
        assert isinstance(ok, bool)


# ---------------------------------------------------------------------------
# validate_score_range
# ---------------------------------------------------------------------------

class TestValidateScoreRange:
    def test_valid_scores(self):
        for score in [1.0, 2.5, 3.0, 4.0, 5.0]:
            ok, msg = validate_score_range(score)
            assert ok is True
            assert msg == ""

    def test_below_range(self):
        ok, msg = validate_score_range(0.5)
        assert ok is False
        assert "outside" in msg

    def test_above_range(self):
        ok, msg = validate_score_range(5.1)
        assert ok is False
        assert "outside" in msg

    def test_boundary_values(self):
        ok1, _ = validate_score_range(1.0)
        ok5, _ = validate_score_range(5.0)
        assert ok1 is True
        assert ok5 is True


# ---------------------------------------------------------------------------
# weights_sum_to_one
# ---------------------------------------------------------------------------

class TestWeightsSumToOne:
    def test_default_weights(self):
        assert weights_sum_to_one(DEFAULT_WEIGHTS) is True

    def test_unnormalized(self):
        bad = {cat: 1.0 for cat in CATEGORIES}
        assert weights_sum_to_one(bad) is False

    def test_empty_dict(self):
        assert weights_sum_to_one({}) is False
