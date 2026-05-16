from __future__ import annotations

from pathlib import Path

import pytest

from eval_harness.environment import (
    VerificationFeedbackEnvironment,
    calculate_reward,
    load_synthetic_cases,
)


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


def test_load_synthetic_cases_returns_valid_cases() -> None:
    cases = load_synthetic_cases(DATASET_PATH)

    assert len(cases) >= 10
    assert cases[0].case_id == "case_001"


def test_environment_can_expose_case_state() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    state = environment.get_state("case_001")

    assert state["device_risk"] == 0.08
    assert state["document_confidence"] == 0.94
    assert state["watchlist_match"] is False


def test_environment_step_returns_reward_result() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    result = environment.step("case_001", "APPROVE")

    assert result.case_id == "case_001"
    assert result.decision == "APPROVE"
    assert result.expected_decision == "APPROVE"
    assert result.reward == 1.0
    assert result.correct is True
    assert result.metadata["reward_reason"] == "correct_decision"


def test_environment_rejects_unknown_case_id() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    with pytest.raises(KeyError):
        environment.get_state("missing_case")


def test_environment_rejects_invalid_action() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    with pytest.raises(ValueError):
        environment.step("case_001", "MANUAL_REVIEW")


def test_environment_requires_at_least_one_case() -> None:
    with pytest.raises(ValueError):
        VerificationFeedbackEnvironment([])