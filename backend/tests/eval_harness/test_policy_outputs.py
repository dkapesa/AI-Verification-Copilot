from __future__ import annotations

from pathlib import Path

import pytest

from eval_harness.environment import load_synthetic_cases
from eval_harness.policies import ai_review_policy, calculate_risk_score, rules_policy
from eval_harness.schemas import VALID_DECISIONS


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


@pytest.fixture
def cases() -> list:
    return load_synthetic_cases(DATASET_PATH)


@pytest.fixture
def cases_by_id(cases: list) -> dict:
    return {case.case_id: case for case in cases}


def test_calculate_risk_score_is_bounded(cases: list) -> None:
    for case in cases:
        risk_score = calculate_risk_score(case)

        assert 0.0 <= risk_score <= 1.0


def test_rules_policy_returns_valid_decision_for_all_cases(cases: list) -> None:
    for case in cases:
        result = rules_policy(case)

        assert result.decision in VALID_DECISIONS
        assert result.policy_name == "rules_policy"
        assert result.case_id == case.case_id
        assert result.confidence is not None
        assert 0.0 <= result.confidence <= 1.0


def test_rules_policy_approves_low_risk_case(cases_by_id: dict) -> None:
    result = rules_policy(cases_by_id["case_001"])

    assert result.decision == "APPROVE"


def test_rules_policy_rejects_watchlist_high_risk_case(cases_by_id: dict) -> None:
    result = rules_policy(cases_by_id["case_003"])

    assert result.decision == "REJECT"


def test_ai_review_policy_uses_mocked_decision_when_provided(cases_by_id: dict) -> None:
    result = ai_review_policy(
        cases_by_id["case_001"],
        mocked_decisions_by_case_id={"case_001": "ESCALATE"},
    )

    assert result.decision == "ESCALATE"
    assert result.policy_name == "ai_review_policy"
    assert result.rationale is not None
    assert "mocked" in result.rationale.lower()


def test_ai_review_policy_returns_valid_decision_for_all_cases(cases: list) -> None:
    for case in cases:
        result = ai_review_policy(case)

        assert result.decision in VALID_DECISIONS
        assert result.policy_name == "ai_review_policy"
        assert result.case_id == case.case_id