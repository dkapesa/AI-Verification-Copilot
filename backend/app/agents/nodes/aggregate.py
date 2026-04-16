from __future__ import annotations

from app.agents.schemas import AggregatedSignal
from app.agents.state import AgentState


def infer_default_severity_from_score(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.4:
        return "moderate"
    return "low"


def normalize_signal_label(signal: object) -> str:
    if isinstance(signal, dict):
        return str(signal.get("code") or signal.get("label") or signal)
    return str(signal)


def normalize_signal_severity(signal: object, tool_score: float) -> str:
    default_severity = infer_default_severity_from_score(tool_score)

    if isinstance(signal, dict):
        raw_severity = signal.get("severity")
        if raw_severity is None:
            return default_severity
        return str(raw_severity).lower()

    return default_severity


def aggregate_node(state_dict: dict) -> dict:
    state = AgentState.model_validate(state_dict)

    if state.errors:
        return {}

    tool_outputs = state.tool_outputs or []

    overall_risk_score = 0.0
    high_risk_flags: list[str] = []
    moderate_risk_flags: list[str] = []
    low_risk_flags: list[str] = []
    tools_failed: list[str] = []
    tool_summaries: list[dict] = []

    for tool in tool_outputs:
        tool_name = tool.get("tool_name", "unknown_tool")
        status = tool.get("status", "UNKNOWN")
        score = float(tool.get("score") or 0.0)

        overall_risk_score = max(overall_risk_score, score)

        tool_summaries.append(
            {
                "tool_name": tool_name,
                "status": status,
                "score": score,
                "confidence": tool.get("confidence"),
                "summary": tool.get("summary"),
            }
        )

        if status != "SUCCESS":
            tools_failed.append(tool_name)

        for signal in tool.get("signals") or []:
            label = normalize_signal_label(signal)
            severity = normalize_signal_severity(signal, score)

            if severity in {"high", "critical"}:
                high_risk_flags.append(label)
            elif severity in {"medium", "moderate"}:
                moderate_risk_flags.append(label)
            else:
                low_risk_flags.append(label)

    aggregated = AggregatedSignal(
        overall_risk_score=min(max(overall_risk_score, 0.0), 1.0),
        high_risk_flags=sorted(set(high_risk_flags)),
        moderate_risk_flags=sorted(set(moderate_risk_flags)),
        low_risk_flags=sorted(set(low_risk_flags)),
        tool_summaries=tool_summaries,
        tools_failed=sorted(set(tools_failed)),
    )

    reasoning_summary = (
        f"Overall risk score={aggregated.overall_risk_score}; "
        f"high={len(aggregated.high_risk_flags)}; "
        f"moderate={len(aggregated.moderate_risk_flags)}; "
        f"low={len(aggregated.low_risk_flags)}; "
        f"failed_tools={len(aggregated.tools_failed)}"
    )

    return {
        "aggregated_signals": aggregated.model_dump(),
        "reasoning_summary": reasoning_summary,
    }