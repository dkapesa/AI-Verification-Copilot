from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.tools.behaviour_anomaly import TOOL_NAME as BEHAVIOUR_ANOMALY_TOOL_NAME
from app.tools.behaviour_anomaly import behaviour_anomaly_check
from app.tools.rules_risk_score import TOOL_NAME as RULES_RISK_SCORE_TOOL_NAME
from app.tools.rules_risk_score import rules_risk_score
from app.tools.watchlist_screening import TOOL_NAME as WATCHLIST_SCREENING_TOOL_NAME
from app.tools.watchlist_screening import watchlist_screening
from app.tools.device_risk import TOOL_NAME as DEVICE_RISK_TOOL_NAME
from app.tools.device_risk import device_risk_check

from app.tools.schemas import ToolCaseInput, ToolResult

ToolCallable = Callable[[ToolCaseInput], Awaitable[ToolResult]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool_fn: ToolCallable) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = tool_fn

    def get(self, name: str) -> ToolCallable:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def all(self) -> dict[str, ToolCallable]:
        return dict(self._tools)


tool_registry = ToolRegistry()
tool_registry.register(DEVICE_RISK_TOOL_NAME, device_risk_check)

tool_registry.register(WATCHLIST_SCREENING_TOOL_NAME, watchlist_screening)
tool_registry.register(BEHAVIOUR_ANOMALY_TOOL_NAME, behaviour_anomaly_check)
tool_registry.register(RULES_RISK_SCORE_TOOL_NAME, rules_risk_score)