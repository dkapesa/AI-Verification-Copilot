# backend/app/agents/nodes/decide.py
from __future__ import annotations

from app.agents.llm import get_decision_provider
from app.agents.prompts import build_decision_input, build_retry_input
from app.agents.state import AgentState


MAX_DECISION_RETRIES = 2


async def decision_node(state_dict: dict) -> dict:
    state = AgentState.model_validate(state_dict)

    if state.errors:
        return {}

    provider = get_decision_provider()

    payload = build_decision_input(
        case_data=state.case_data or {},
        aggregated_signals=(state.aggregated_signals.model_dump() if hasattr(state.aggregated_signals, "model_dump") else state.aggregated_signals or {}),
    )

    last_error = None
    for attempt in range(MAX_DECISION_RETRIES):
        try:
            if attempt == 0:
                decision = await provider.generate_decision(payload)
            else:
                retry_payload = build_retry_input(
                    original_payload=payload,
                    validation_error=str(last_error),
                )
                decision = await provider.generate_decision(retry_payload)

            return {
                "decision": decision.model_dump(),
                "retry_count": attempt,
                "model_provider": "openai",
                "model_name": getattr(provider, "model", None),
            }
        except Exception as exc:
            last_error = exc

    return {
        "errors": [f"Decision node failed after retries: {last_error}"],
        "retry_count": MAX_DECISION_RETRIES,
        "model_provider": "openai",
        "model_name": getattr(provider, "model", None),
    }