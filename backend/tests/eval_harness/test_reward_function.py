from __future__ import annotations

from pathlib import Path

import pytest

from eval_harness.environment import calculate_reward, load_synthetic_cases


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


def test_correct_approve_receives_full_positive_reward(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_001"], "APPROVE")

    assert reward == 1.0
    assert metadata["reward_reason"] == "correct_decision"


def test_correct_reject_receives_full_positive_reward(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_003"], "REJECT")

    assert reward == 1.0
    assert metadata["reward_reason"] == "correct_decision"


def test_correct_escalation_receives_partial_positive_reward(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_002"], "ESCALATE")

    assert reward == 0.5
    assert metadata["reward_reason"] == "appropriate_escalation"


def test_false_approve_confirmed_fraud_is_highest_cost(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_003"], "APPROVE")

    assert reward == -2.0
    assert metadata["reward_reason"] == "false_approve_confirmed_fraud"


def test_false_reject_legitimate_case_is_penalized(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_001"], "REJECT")

    assert reward == -1.0
    assert metadata["reward_reason"] == "false_reject_legitimate_case"


def test_unnecessary_escalation_has_smaller_operational_penalty(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_001"], "ESCALATE")

    assert reward == -0.3
    assert metadata["reward_reason"] == "unnecessary_escalation"


def test_approving_uncertain_case_is_penalized(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_002"], "APPROVE")

    assert reward == -0.8
    assert metadata["reward_reason"] == "approved_case_needing_manual_review"


def test_rejecting_uncertain_case_is_penalized(cases_by_id: dict) -> None:
    reward, metadata = calculate_reward(cases_by_id["case_002"], "REJECT")

    assert reward == -0.5
    assert metadata["reward_reason"] == "rejected_uncertain_case"


def test_invalid_action_raises_value_error(cases_by_id: dict) -> None:
    with pytest.raises(ValueError):
        calculate_reward(cases_by_id["case_001"], "MANUAL_REVIEW")