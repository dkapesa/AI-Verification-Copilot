from __future__ import annotations

import asyncio
from typing import Any

from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus

TOOL_NAME = "device_risk_check"


async def device_risk_check(case_input: ToolCaseInput) -> ToolResult:
    """
    Deterministic device risk evaluation.
    This tool inspects device metadata and produces a risk score.
    """

    await asyncio.sleep(0)

    device = case_input.device_info or {}

    score = 0.0
    signals: dict[str, Any] = {}
    triggered_rules: list[str] = []

    if device.get("is_emulator"):
        score += 0.35
        signals["is_emulator"] = True
        triggered_rules.append("emulator_detected")

    if device.get("is_rooted") or device.get("is_jailbroken"):
        score += 0.30
        signals["rooted_device"] = True
        triggered_rules.append("rooted_device")

    if device.get("vpn_detected") or device.get("proxy_detected"):
        score += 0.20
        signals["vpn_or_proxy"] = True
        triggered_rules.append("vpn_or_proxy")

    account_count = device.get("account_count_on_device")

    if account_count and account_count >= 3:
        score += 0.15
        signals["account_count_on_device"] = account_count
        triggered_rules.append("many_accounts_on_device")

    device_age_days = device.get("device_age_days")

    if device_age_days is not None and device_age_days < 7:
        score += 0.10
        signals["device_age_days"] = device_age_days
        triggered_rules.append("new_device")

    score = min(score, 1.0)

    if score >= 0.75:
        summary = "High device risk based on multiple suspicious signals."
    elif score >= 0.40:
        summary = "Moderate device risk detected."
    else:
        summary = "Low device risk."

    confidence = 0.70 + (len(signals) * 0.05)
    confidence = min(confidence, 0.95)

    return ToolResult(
        tool_name=TOOL_NAME,
        status=ToolRunStatus.SUCCESS,
        score=score,
        confidence=confidence,
        summary=summary,
        signals=signals,
        output={
            "triggered_rules": triggered_rules,
            "signal_count": len(signals),
        },
    )