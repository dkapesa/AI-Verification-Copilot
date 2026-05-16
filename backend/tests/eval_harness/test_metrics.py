from __future__ import annotations

from pathlib import Path

from eval_harness.environment import VerificationFeedbackEnvironment
from eval_harness.metrics import summarize_results


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


def test_summarize_results_calculates_core_metrics() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    results = [
        environment.step("case_001", "APPROVE"),
        environment.step("case_003", "APPROVE"),
        environment.step("case_001", "REJECT"),
        environment.step("case_002", "ESCALATE"),
    ]

    metrics = summarize_results(results, failure_count=0, runtime_seconds=0.12)

    assert metrics["total_cases"] == 4
    assert metrics["correct_count"] == 2
    assert metrics["accuracy"] == 0.5
    assert metrics["average_reward"] == -0.375
    assert metrics["false_approve_count"] == 1
    assert metrics["false_approve_rate"] == 0.25
    assert metrics["false_reject_count"] == 1
    assert metrics["false_reject_rate"] == 0.25
    assert metrics["escalation_count"] == 1
    assert metrics["escalation_rate"] == 0.25
    assert metrics["failure_count"] == 0
    assert metrics["runtime_seconds"] == 0.12


def test_summarize_results_handles_empty_results() -> None:
    metrics = summarize_results([], failure_count=2, runtime_seconds=0.01)

    assert metrics["total_cases"] == 0
    assert metrics["accuracy"] == 0.0
    assert metrics["average_reward"] == 0.0
    assert metrics["failure_count"] == 2
    assert metrics["decision_distribution"] == {
        "APPROVE": 0,
        "ESCALATE": 0,
        "REJECT": 0,
    }


def test_summarize_results_includes_decision_distribution() -> None:
    environment = VerificationFeedbackEnvironment.from_jsonl(DATASET_PATH)

    results = [
        environment.step("case_001", "APPROVE"),
        environment.step("case_002", "ESCALATE"),
        environment.step("case_003", "REJECT"),
    ]

    metrics = summarize_results(results)

    assert metrics["decision_distribution"] == {
        "APPROVE": 1,
        "ESCALATE": 1,
        "REJECT": 1,
    }
    assert metrics["decision_distribution_rate"] == {
        "APPROVE": 1 / 3,
        "ESCALATE": 1 / 3,
        "REJECT": 1 / 3,
    }