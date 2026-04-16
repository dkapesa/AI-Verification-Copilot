from __future__ import annotations

import asyncio
from typing import Any

from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus

TOOL_NAME = "rules_risk_score"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


async def rules_risk_score(case_input: ToolCaseInput) -> ToolResult:
    await asyncio.sleep(0)

    device = case_input.device_info or {}
    document = case_input.document_check_result or {}
    behaviour = case_input.behaviour_summary or {}

    signals: dict[str, Any] = {}
    triggered_rules: list[str] = []
    score = 0.0

    if _as_bool(device.get("is_emulator")):
        score += 0.20
        signals["device_emulator"] = True
        triggered_rules.append("device_emulator")

    if _as_bool(device.get("vpn_detected")) or _as_bool(device.get("proxy_detected")):
        score += 0.15
        signals["network_obfuscation"] = True
        triggered_rules.append("network_obfuscation")

    if document.get("passed") is False or document.get("document_valid") is False:
        score += 0.35
        signals["document_check_failed"] = True
        triggered_rules.append("document_check_failed")

    if behaviour.get("automation_score") is not None and float(behaviour["automation_score"]) >= 0.80:
        score += 0.25
        signals["high_automation_score"] = float(behaviour["automation_score"])
        triggered_rules.append("high_automation_score")

    if behaviour.get("repeated_verification_attempts") is not None and int(behaviour["repeated_verification_attempts"]) >= 3:
        score += 0.20
        signals["repeated_verification_attempts"] = int(behaviour["repeated_verification_attempts"])
        triggered_rules.append("repeated_verification_attempts")

    score = min(score, 1.0)

    if score >= 0.75:
        summary = "High rules-based fraud risk based on multiple cross-signal indicators."
    elif score >= 0.40:
        summary = "Moderate rules-based fraud risk; manual review may be warranted."
    else:
        summary = "Low rules-based fraud risk from current structured signals."

    confidence = 0.85

    return ToolResult(
        tool_name=TOOL_NAME,
        status=ToolRunStatus.SUCCESS,
        score=score,
        confidence=confidence,
        summary=summary,
        signals=signals,
        output={
            "triggered_rules": triggered_rules,
            "rule_count": len(triggered_rules),
        },
    )