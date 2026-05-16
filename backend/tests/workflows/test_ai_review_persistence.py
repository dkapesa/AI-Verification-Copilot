import time
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.agents.nodes.persist import (
    build_persist_node,
    categorize_error_message,
    sanitize_error_message,
)
from app.agents.schemas import AggregatedSignal, DecisionOutput
from app.agents.state import AgentState
from app.db.models.ai_review import AIReview
from app.db.models.audit_log import AuditLog


def _successful_agent_state(case_id):
    return AgentState(
        case_id=case_id,
        tool_outputs=[
            {
                "tool_name": "device_risk_check",
                "status": "SUCCESS",
                "score": 0.18,
                "confidence": 0.94,
                "summary": "Low device risk.",
            }
        ],
        aggregated_signals=AggregatedSignal(
            overall_risk_score=0.18,
            high_risk_flags=[],
            moderate_risk_flags=[],
            low_risk_flags=["document_valid", "normal_login_velocity"],
            tool_summaries=[
                {
                    "tool_name": "device_risk_check",
                    "status": "SUCCESS",
                    "score": 0.18,
                    "confidence": 0.94,
                    "summary": "Low device risk.",
                }
            ],
            tools_failed=[],
        ),
        decision=DecisionOutput(
            decision="APPROVE",
            confidence=0.94,
            reasons=["Document checks passed and deterministic signals are low risk."],
            recommended_next_steps=["Approve verification."],
        ),
        reasoning_summary="Overall risk score=0.18; high=0; moderate=0; low=2; failed_tools=0",
        errors=[],
        retry_count=1,
        model_provider="test-provider",
        model_name="mock-review-model",
        prompt_version="test-v1",
        started_at_ms=int(time.time() * 1000) - 250,
    )


def _failed_agent_state(case_id, errors=None):
    return AgentState(
        case_id=case_id,
        tool_outputs=[],
        aggregated_signals=None,
        decision=None,
        reasoning_summary=None,
        errors=errors or ["invalid_api_key: incorrect api key provided"],
        retry_count=2,
        model_provider="test-provider",
        model_name="mock-review-model",
        prompt_version="test-v1",
        started_at_ms=int(time.time() * 1000) - 250,
    )


def test_persist_node_saves_successful_ai_review(db_session):
    case_id = uuid4()
    persist_node = build_persist_node(db_session)

    result = persist_node(_successful_agent_state(case_id).model_dump())

    review = db_session.scalar(
        select(AIReview).where(AIReview.case_id == case_id)
    )

    assert review is not None
    assert review.case_id == case_id
    assert review.decision == "APPROVE"
    assert review.confidence == 0.94
    assert review.reasons == [
        "Document checks passed and deterministic signals are low risk."
    ]
    assert review.recommended_next_steps == ["Approve verification."]
    assert review.aggregated_signals["overall_risk_score"] == 0.18
    assert review.aggregated_signals["low_risk_flags"] == [
        "document_valid",
        "normal_login_velocity",
    ]
    assert review.reasoning_summary == (
        "Overall risk score=0.18; high=0; moderate=0; low=2; failed_tools=0"
    )
    assert review.model_provider == "test-provider"
    assert review.model_name == "mock-review-model"
    assert review.prompt_version == "test-v1"
    assert review.retry_count == 1
    assert review.latency_ms is not None
    assert review.latency_ms >= 0

    assert result["completed_at_ms"] is not None
    assert result["latency_ms"] is not None
    assert result["latency_ms"] >= 0


def test_persist_node_writes_completed_audit_event(db_session):
    case_id = uuid4()
    persist_node = build_persist_node(db_session)

    persist_node(_successful_agent_state(case_id).model_dump())

    audit_log = db_session.scalar(
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .where(AuditLog.event_type == "AI_REVIEW_COMPLETED")
    )

    assert audit_log is not None
    assert audit_log.actor_type == "SYSTEM"
    assert audit_log.subject == "ai_review"
    assert audit_log.latency_ms is not None
    assert audit_log.latency_ms >= 0
    assert audit_log.meta["decision"] == "APPROVE"
    assert audit_log.meta["confidence"] == 0.94
    assert audit_log.meta["retry_count"] == 1
    assert audit_log.meta["model_provider"] == "test-provider"
    assert audit_log.meta["model_name"] == "mock-review-model"


def test_persist_node_does_not_save_ai_review_when_state_has_errors(db_session):
    case_id = uuid4()
    persist_node = build_persist_node(db_session)

    persist_node(_failed_agent_state(case_id).model_dump())

    review = db_session.scalar(
        select(AIReview).where(AIReview.case_id == case_id)
    )

    assert review is None


def test_persist_node_writes_failed_audit_event_with_sanitized_error(db_session):
    case_id = uuid4()
    persist_node = build_persist_node(db_session)

    persist_node(
        _failed_agent_state(
            case_id,
            errors=["invalid_api_key: incorrect api key provided: sk-test-secret"],
        ).model_dump()
    )

    audit_log = db_session.scalar(
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .where(AuditLog.event_type == "AI_REVIEW_FAILED")
    )

    assert audit_log is not None
    assert audit_log.actor_type == "SYSTEM"
    assert audit_log.subject == "ai_review"
    assert audit_log.latency_ms is not None
    assert audit_log.latency_ms >= 0

    assert audit_log.meta["error_category"] == "AUTHENTICATION_ERROR"
    assert audit_log.meta["retry_count"] == 2
    assert audit_log.meta["model_provider"] == "test-provider"
    assert audit_log.meta["model_name"] == "mock-review-model"

    sanitized_errors = audit_log.meta["errors"]

    assert sanitized_errors == [
        "AI review failed after retries due to provider authentication error. "
        "Check backend model credentials/configuration."
    ]
    assert "sk-test-secret" not in str(sanitized_errors)
    assert "incorrect api key provided" not in str(sanitized_errors).lower()


@pytest.mark.parametrize(
    ("raw_error", "expected_category", "expected_sanitized_message"),
    [
        (
            "invalid_api_key: incorrect api key provided",
            "AUTHENTICATION_ERROR",
            "AI review failed after retries due to provider authentication error. "
            "Check backend model credentials/configuration.",
        ),
        (
            "429 rate limit exceeded",
            "RATE_LIMIT_ERROR",
            "AI review failed after retries due to provider rate limiting. "
            "Retry later or adjust provider usage limits.",
        ),
        (
            "request timeout while calling provider",
            "TIMEOUT_ERROR",
            "AI review failed after retries due to an upstream timeout. "
            "Check provider availability and retry.",
        ),
        (
            "connection refused while calling provider",
            "UPSTREAM_CONNECTION_ERROR",
            "AI review failed after retries due to an upstream connection issue. "
            "Check provider/network configuration.",
        ),
        (
            "unexpected provider response",
            "AI_REVIEW_ERROR",
            "AI review failed after retries. Check backend logs for detailed error context.",
        ),
    ],
)
def test_ai_review_error_messages_are_categorized_and_sanitized(
    raw_error,
    expected_category,
    expected_sanitized_message,
):
    assert categorize_error_message(raw_error) == expected_category
    assert sanitize_error_message(raw_error) == expected_sanitized_message