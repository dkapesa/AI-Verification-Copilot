# backend/app/agents/prompts.py
from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "v1"


SYSTEM_PROMPT = """
You are an identity verification and fraud review decision engine.

Your job is to review verification case evidence and produce a structured decision.

Rules:
- Use only the evidence provided.
- Do not invent facts.
- If the evidence is ambiguous, incomplete, or mixed, prefer ESCALATE.
- APPROVE only when risk is clearly low.
- REJECT only when there are strong indicators of fraud, severe contradictions, or highly adverse signals.
- Keep reasons concise, specific, and grounded in the provided tool outputs and case data.
- recommended_next_steps should be practical actions for ops or review teams.
""".strip()


def build_decision_input(
    *,
    case_data: dict[str, Any],
    aggregated_signals: dict[str, Any],
) -> str:
    payload = {
        "rubric": {
            "APPROVE": "Low risk. No meaningful adverse signals. Evidence is internally consistent.",
            "ESCALATE": "Mixed, ambiguous, suspicious, or incomplete signals that require human review.",
            "REJECT": "Strong fraud indicators, severe contradictions, confirmed watchlist risk, or multiple high-risk findings.",
        },
        "case_data": case_data,
        "aggregated_signals": aggregated_signals,
        "required_output": {
            "decision": "APPROVE | ESCALATE | REJECT",
            "confidence": "float between 0 and 1",
            "reasons": ["list of concise evidence-based reasons"],
            "recommended_next_steps": ["list of practical follow-up actions"],
        },
    }
    return json.dumps(payload, indent=2, default=str)


def build_retry_input(
    *,
    original_payload: str,
    validation_error: str,
) -> str:
    return f"""
Your previous response did not satisfy the required schema.

Validation error:
{validation_error}

Return a corrected response using the exact required schema and only supported values.

Original review payload:
{original_payload}
""".strip()