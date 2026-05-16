import pytest
from pydantic import ValidationError

from app.agents.schemas import AggregatedSignal, AIReviewResponse, DecisionOutput


def _valid_aggregated_signals() -> AggregatedSignal:
    return AggregatedSignal(
        overall_risk_score=0.42,
        high_risk_flags=[],
        moderate_risk_flags=["device_velocity_moderate"],
        low_risk_flags=["document_valid"],
        tool_summaries=[
            {
                "tool_name": "device_risk_check",
                "status": "SUCCESS",
                "score": 0.35,
                "summary": "No high-risk device indicators found.",
            }
        ],
        tools_failed=[],
    )


def test_valid_approve_decision_output_schema_passes():
    decision = DecisionOutput(
        decision="APPROVE",
        confidence=0.91,
        reasons=["Signals are low risk and document checks passed."],
        recommended_next_steps=["Approve verification."],
    )

    assert decision.decision == "APPROVE"
    assert decision.confidence == 0.91
    assert decision.reasons == ["Signals are low risk and document checks passed."]


def test_valid_escalate_decision_output_schema_passes():
    decision = DecisionOutput(
        decision="ESCALATE",
        confidence=0.74,
        reasons=["Some signals require manual analyst review."],
        recommended_next_steps=["Escalate to fraud operations queue."],
    )

    assert decision.decision == "ESCALATE"
    assert decision.confidence == 0.74


def test_valid_reject_decision_output_schema_passes():
    decision = DecisionOutput(
        decision="REJECT",
        confidence=0.89,
        reasons=["High-risk watchlist and device indicators were detected."],
        recommended_next_steps=["Reject verification and document rationale."],
    )

    assert decision.decision == "REJECT"
    assert decision.confidence == 0.89


def test_decision_output_rejects_invalid_decision_value():
    with pytest.raises(ValidationError):
        DecisionOutput(
            decision="MANUAL_REVIEW",
            confidence=0.8,
            reasons=["Invalid decision value should not be accepted."],
            recommended_next_steps=["This should fail validation."],
        )


def test_decision_output_rejects_confidence_below_zero():
    with pytest.raises(ValidationError):
        DecisionOutput(
            decision="APPROVE",
            confidence=-0.01,
            reasons=["Confidence must be between zero and one."],
            recommended_next_steps=[],
        )


def test_decision_output_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        DecisionOutput(
            decision="APPROVE",
            confidence=1.01,
            reasons=["Confidence must be between zero and one."],
            recommended_next_steps=[],
        )


def test_decision_output_requires_at_least_one_reason():
    with pytest.raises(ValidationError):
        DecisionOutput(
            decision="ESCALATE",
            confidence=0.7,
            reasons=[],
            recommended_next_steps=["Escalate for analyst review."],
        )


def test_aggregated_signal_schema_rejects_risk_score_below_zero():
    with pytest.raises(ValidationError):
        AggregatedSignal(overall_risk_score=-0.01)


def test_aggregated_signal_schema_rejects_risk_score_above_one():
    with pytest.raises(ValidationError):
        AggregatedSignal(overall_risk_score=1.01)


def test_valid_completed_ai_review_response_schema_passes():
    response = AIReviewResponse(
        case_id="case-123",
        status="COMPLETED",
        decision=DecisionOutput(
            decision="ESCALATE",
            confidence=0.77,
            reasons=["Moderate risk indicators require analyst review."],
            recommended_next_steps=["Request manual review."],
        ),
        aggregated_signals=_valid_aggregated_signals(),
        tool_results_count=4,
        errors=[],
    )

    assert response.case_id == "case-123"
    assert response.status == "COMPLETED"
    assert response.decision is not None
    assert response.decision.decision == "ESCALATE"
    assert response.aggregated_signals is not None
    assert response.tool_results_count == 4
    assert response.errors == []


def test_valid_failed_ai_review_response_schema_passes_without_decision():
    response = AIReviewResponse(
        case_id="case-123",
        status="FAILED",
        decision=None,
        aggregated_signals=None,
        tool_results_count=0,
        errors=["Model response could not be parsed."],
    )

    assert response.status == "FAILED"
    assert response.decision is None
    assert response.aggregated_signals is None
    assert response.errors == ["Model response could not be parsed."]


def test_ai_review_response_rejects_invalid_status():
    with pytest.raises(ValidationError):
        AIReviewResponse(
            case_id="case-123",
            status="PENDING",
            decision=None,
            aggregated_signals=None,
            tool_results_count=0,
            errors=[],
        )