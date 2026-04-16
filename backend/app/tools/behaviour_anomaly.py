from __future__ import annotations

import asyncio
from typing import Any

from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus

TOOL_NAME = "behaviour_anomaly_check"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def behaviour_anomaly_check(case_input: ToolCaseInput) -> ToolResult:
    await asyncio.sleep(0)

    behaviour = case_input.behaviour_summary or {}

    signals: dict[str, Any] = {}
    triggered_rules: list[str] = []
    score = 0.0

    typing_speed_wpm = _as_float(behaviour.get("typing_speed_wpm"))
    if typing_speed_wpm > 140:
        score += 0.25
        signals["typing_speed_wpm"] = typing_speed_wpm
        triggered_rules.append("abnormally_fast_typing")

    repeated_attempts = _as_int(behaviour.get("repeated_verification_attempts"))
    if repeated_attempts >= 3:
        score += 0.30
        signals["repeated_verification_attempts"] = repeated_attempts
        triggered_rules.append("repeated_verification_attempts")

    session_duration_seconds = _as_int(behaviour.get("session_duration_seconds"))
    if 0 < session_duration_seconds < 15:
        score += 0.20
        signals["session_duration_seconds"] = session_duration_seconds
        triggered_rules.append("very_short_session")

    automation_score = _as_float(behaviour.get("automation_score"))
    if automation_score >= 0.80:
        score += 0.35
        signals["automation_score"] = automation_score
        triggered_rules.append("high_automation_score")

    score = min(score, 1.0)

    if score >= 0.70:
        summary = "High behavioural anomaly risk based on strong automation-like patterns."
    elif score >= 0.35:
        summary = "Moderate behavioural anomaly risk with suspicious interaction signals."
    else:
        summary = "Low behavioural anomaly risk from available session data."

    populated_fields = sum(
        1
        for value in [
            behaviour.get("typing_speed_wpm"),
            behaviour.get("repeated_verification_attempts"),
            behaviour.get("session_duration_seconds"),
            behaviour.get("automation_score"),
        ]
        if value is not None
    )
    confidence = min(0.60 + (populated_fields * 0.08), 0.92)

    return ToolResult(
        tool_name=TOOL_NAME,
        status=ToolRunStatus.SUCCESS,
        score=score,
        confidence=confidence,
        summary=summary,
        signals=signals,
        output={
            "triggered_rules": triggered_rules,
            "match_count": len(triggered_rules),
            "behaviour_snapshot": {
                "typing_speed_wpm": typing_speed_wpm,
                "repeated_verification_attempts": repeated_attempts,
                "session_duration_seconds": session_duration_seconds,
                "automation_score": automation_score,
            },
        },
    )