# backend/app/agents/nodes/planner.py
from __future__ import annotations

from app.agents.state import AgentState


DEFAULT_TOOL_PLAN = [
    "device_risk_check",
    "rules_risk_score",
    "watchlist_screening",
    "behaviour_anomaly_check",
]


def planner_node(state_dict: dict) -> dict:
    state = AgentState.model_validate(state_dict)

    if state.errors:
        return {}

    case_data = state.case_data or {}
    behaviour_summary = case_data.get("behaviour_summary") or {}

    requested_tools = [
        "device_risk_check",
        "rules_risk_score",
        "watchlist_screening",
    ]

    if behaviour_summary:
        requested_tools.append("behaviour_anomaly_check")

    return {"requested_tools": requested_tools}