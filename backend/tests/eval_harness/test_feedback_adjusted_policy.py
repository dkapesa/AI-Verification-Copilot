from __future__ import annotations

from pathlib import Path

import pytest

from eval_harness.environment import calculate_reward, load_synthetic_cases
from eval_harness.policies import FeedbackAdjustedPolicy
from eval_harness.schemas import VALID_DECISIONS


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


@pytest.fixture
def cases_by_id() -> dict:
    cases = load_synthetic_cases(DATASET_PATH)
    return {case.case_id: case for case in cases}


def test_feedback_adjusted_policy_returns_valid_decision(cases_by_id: dict) -> None:
    policy = FeedbackAdjustedPolicy()

    result = policy.decide(cases_by_id["case_001"])

    assert result.decision in VALID_DECISIONS
    assert result.policy_name == "feedback_adjusted_policy"
    assert result.confidence is not None


def test_feedback_adjusted_policy_rejects_invalid_threshold_order() -> None:
    with pytest.raises(ValueError):
        FeedbackAdjustedPolicy(approve_threshold=0.80, reject_threshold=0.70)


def test_feedback_adjusted_policy_lowers_approve_threshold_after_false_approve(
    cases_by_id: dict,
) -> None:
    policy = FeedbackAdjustedPolicy(approve_threshold=0.45, reject_threshold=0.78)
    case = cases_by_id["case_003"]

    reward, _ = calculate_reward(case, "APPROVE")
    old_threshold = policy.approve_threshold

    policy.update(case=case, decision="APPROVE", reward=reward)

    assert reward == -2.0
    assert policy.approve_threshold < old_threshold


def test_feedback_adjusted_policy_raises_reject_threshold_after_false_reject(
    cases_by_id: dict,
) -> None:
    policy = FeedbackAdjustedPolicy(approve_threshold=0.45, reject_threshold=0.78)
    case = cases_by_id["case_001"]

    reward, _ = calculate_reward(case, "REJECT")
    old_threshold = policy.reject_threshold

    policy.update(case=case, decision="REJECT", reward=reward)

    assert reward == -1.0
    assert policy.reject_threshold > old_threshold


def test_feedback_adjusted_policy_tracks_update_history(cases_by_id: dict) -> None:
    policy = FeedbackAdjustedPolicy()
    case = cases_by_id["case_003"]

    reward, _ = calculate_reward(case, "APPROVE")
    policy.update(case=case, decision="APPROVE", reward=reward)

    assert len(policy.history) == 1
    assert policy.history[0]["case_id"] == "case_003"
    assert policy.history[0]["decision"] == "APPROVE"
    assert policy.history[0]["expected_decision"] == "REJECT"


def test_feedback_adjusted_policy_keeps_thresholds_bounded(cases_by_id: dict) -> None:
    policy = FeedbackAdjustedPolicy(approve_threshold=0.06, reject_threshold=0.94)
    case = cases_by_id["case_003"]

    for _ in range(20):
        reward, _ = calculate_reward(case, "APPROVE")
        policy.update(case=case, decision="APPROVE", reward=reward)

    assert 0.05 <= policy.approve_threshold <= 0.90
    assert 0.10 <= policy.reject_threshold <= 0.95
    assert policy.approve_threshold < policy.reject_threshold