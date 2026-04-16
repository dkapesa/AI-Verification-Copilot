from __future__ import annotations

import asyncio
from typing import Any

from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus

TOOL_NAME = "watchlist_screening"

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "tempmail.com",
    "guerrillamail.com",
}

FLAGGED_EMAILS = {
    "fraud@test.com",
    "blocked@example.com",
}

FLAGGED_USER_IDS = {
    "user_watch_001",
    "fraudster_123",
}


async def watchlist_screening(case_input: ToolCaseInput) -> ToolResult:
    await asyncio.sleep(0)

    signals: dict[str, Any] = {}
    triggered_rules: list[str] = []
    score = 0.0

    email = str(case_input.email).lower()
    domain = email.split("@")[-1] if "@" in email else ""

    if email in FLAGGED_EMAILS:
        score += 0.70
        signals["flagged_email"] = email
        triggered_rules.append("flagged_email_match")

    if case_input.user_id in FLAGGED_USER_IDS:
        score += 0.60
        signals["flagged_user_id"] = case_input.user_id
        triggered_rules.append("flagged_user_id_match")

    if domain in DISPOSABLE_EMAIL_DOMAINS:
        score += 0.35
        signals["disposable_email_domain"] = domain
        triggered_rules.append("disposable_email_domain")

    score = min(score, 1.0)

    if score >= 0.70:
        summary = "High watchlist risk due to direct match with flagged identifiers."
    elif score >= 0.35:
        summary = "Moderate watchlist risk due to suspicious email characteristics."
    else:
        summary = "No meaningful watchlist indicators detected."

    confidence = 0.90 if triggered_rules else 0.80

    return ToolResult(
        tool_name=TOOL_NAME,
        status=ToolRunStatus.SUCCESS,
        score=score,
        confidence=confidence,
        summary=summary,
        signals=signals,
        output={
            "triggered_rules": triggered_rules,
            "email_domain": domain,
            "match_count": len(triggered_rules),
        },
    )