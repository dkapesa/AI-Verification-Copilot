from __future__ import annotations

from eval_harness.schemas import EvaluationStepResult


DECISION_ORDER = ["APPROVE", "ESCALATE", "REJECT"]


def _safe_rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return count / total


def summarize_results(
    results: list[EvaluationStepResult],
    *,
    failure_count: int = 0,
    runtime_seconds: float | None = None,
) -> dict:
    """
    Summarize policy evaluation results.

    Metrics are intentionally simple and inspectable. They are designed for
    lightweight policy comparison, not for claiming production model quality.
    """
    total_cases = len(results)

    if total_cases == 0:
        return {
            "total_cases": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "average_reward": 0.0,
            "false_approve_count": 0,
            "false_approve_rate": 0.0,
            "false_reject_count": 0,
            "false_reject_rate": 0.0,
            "escalation_count": 0,
            "escalation_rate": 0.0,
            "decision_distribution": {decision: 0 for decision in DECISION_ORDER},
            "decision_distribution_rate": {decision: 0.0 for decision in DECISION_ORDER},
            "failure_count": failure_count,
            "runtime_seconds": runtime_seconds,
        }

    correct_count = sum(1 for result in results if result.correct)
    total_reward = sum(result.reward for result in results)

    false_approve_count = sum(
        1
        for result in results
        if result.decision == "APPROVE" and result.expected_decision != "APPROVE"
    )

    false_reject_count = sum(
        1
        for result in results
        if result.decision == "REJECT" and result.expected_decision != "REJECT"
    )

    escalation_count = sum(1 for result in results if result.decision == "ESCALATE")

    decision_distribution = {
        decision: sum(1 for result in results if result.decision == decision)
        for decision in DECISION_ORDER
    }

    decision_distribution_rate = {
        decision: _safe_rate(count, total_cases)
        for decision, count in decision_distribution.items()
    }

    return {
        "total_cases": total_cases,
        "correct_count": correct_count,
        "accuracy": correct_count / total_cases,
        "average_reward": total_reward / total_cases,
        "false_approve_count": false_approve_count,
        "false_approve_rate": false_approve_count / total_cases,
        "false_reject_count": false_reject_count,
        "false_reject_rate": false_reject_count / total_cases,
        "escalation_count": escalation_count,
        "escalation_rate": escalation_count / total_cases,
        "decision_distribution": decision_distribution,
        "decision_distribution_rate": decision_distribution_rate,
        "failure_count": failure_count,
        "runtime_seconds": runtime_seconds,
    }