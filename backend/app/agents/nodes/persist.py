from __future__ import annotations

import time
from typing import Iterable

from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.core.audit import write_audit_log
from app.crud.ai_review import create_ai_review


def categorize_error_message(message: str) -> str:
    normalized = message.lower()

    if "invalid_api_key" in normalized or "incorrect api key provided" in normalized:
        return "AUTHENTICATION_ERROR"

    if "rate limit" in normalized or "429" in normalized:
        return "RATE_LIMIT_ERROR"

    if "timeout" in normalized:
        return "TIMEOUT_ERROR"

    if "connection" in normalized or "connect" in normalized:
        return "UPSTREAM_CONNECTION_ERROR"

    return "AI_REVIEW_ERROR"


def sanitize_error_message(message: str) -> str:
    normalized = message.lower()

    if "invalid_api_key" in normalized or "incorrect api key provided" in normalized:
        return (
            "AI review failed after retries due to provider authentication error. "
            "Check backend model credentials/configuration."
        )

    if "rate limit" in normalized or "429" in normalized:
        return (
            "AI review failed after retries due to provider rate limiting. "
            "Retry later or adjust provider usage limits."
        )

    if "timeout" in normalized:
        return (
            "AI review failed after retries due to an upstream timeout. "
            "Check provider availability and retry."
        )

    if "connection" in normalized or "connect" in normalized:
        return (
            "AI review failed after retries due to an upstream connection issue. "
            "Check provider/network configuration."
        )

    return "AI review failed after retries. Check backend logs for detailed error context."


def sanitize_errors(errors: Iterable[str] | None) -> list[str]:
    if not errors:
      return ["AI review failed. Check backend logs for details."]

    sanitized = []
    for error in errors:
        if isinstance(error, str) and error.strip():
            sanitized.append(sanitize_error_message(error))

    return sanitized or ["AI review failed. Check backend logs for details."]


def build_persist_node(db: Session):
    def persist_node(state_dict: dict) -> dict:
        state = AgentState.model_validate(state_dict)

        completed_at_ms = int(time.time() * 1000)
        latency_ms = None
        if state.started_at_ms is not None:
            latency_ms = completed_at_ms - state.started_at_ms

        if state.decision and not state.errors:
            create_ai_review(
                db=db,
                case_id=state.case_id,
                decision=state.decision.decision,
                confidence=state.decision.confidence,
                reasons=state.decision.reasons,
                recommended_next_steps=state.decision.recommended_next_steps,
                aggregated_signals=(
                    state.aggregated_signals.model_dump()
                    if state.aggregated_signals
                    else {}
                ),
                reasoning_summary=state.reasoning_summary,
                model_provider=state.model_provider,
                model_name=state.model_name,
                prompt_version=state.prompt_version,
                retry_count=state.retry_count,
                latency_ms=latency_ms,
            )

            write_audit_log(
                db=db,
                case_id=state.case_id,
                event_type="AI_REVIEW_COMPLETED",
                actor_type="SYSTEM",
                subject="ai_review",
                latency_ms=latency_ms,
                metadata={
                    "decision": state.decision.decision,
                    "confidence": state.decision.confidence,
                    "retry_count": state.retry_count,
                    "model_provider": state.model_provider,
                    "model_name": state.model_name,
                },
            )
        else:
            sanitized_errors = sanitize_errors(state.errors)
            error_category = (
                categorize_error_message(state.errors[0])
                if state.errors and isinstance(state.errors[0], str)
                else "AI_REVIEW_ERROR"
            )

            write_audit_log(
                db=db,
                case_id=state.case_id,
                event_type="AI_REVIEW_FAILED",
                actor_type="SYSTEM",
                subject="ai_review",
                latency_ms=latency_ms,
                metadata={
                    "errors": sanitized_errors,
                    "error_category": error_category,
                    "retry_count": state.retry_count,
                    "model_provider": state.model_provider,
                    "model_name": state.model_name,
                },
            )

        return {
            "completed_at_ms": completed_at_ms,
            "latency_ms": latency_ms,
        }

    return persist_node