import pytest

from app.tools.behaviour_anomaly import TOOL_NAME as BEHAVIOUR_ANOMALY_TOOL_NAME
from app.tools.device_risk import TOOL_NAME as DEVICE_RISK_TOOL_NAME
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.rules_risk_score import TOOL_NAME as RULES_RISK_SCORE_TOOL_NAME
from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus
from app.tools.watchlist_screening import TOOL_NAME as WATCHLIST_SCREENING_TOOL_NAME


async def _dummy_tool(case_input: ToolCaseInput) -> ToolResult:
    return ToolResult(
        tool_name="dummy_tool",
        status=ToolRunStatus.SUCCESS,
        score=0.0,
        confidence=1.0,
        summary="Dummy tool completed.",
    )


def test_expected_tools_are_registered():
    expected_tool_names = {
        DEVICE_RISK_TOOL_NAME,
        WATCHLIST_SCREENING_TOOL_NAME,
        BEHAVIOUR_ANOMALY_TOOL_NAME,
        RULES_RISK_SCORE_TOOL_NAME,
    }

    registered_tool_names = set(tool_registry.list_names())

    assert registered_tool_names == expected_tool_names


def test_registry_reports_known_and_unknown_tools():
    assert tool_registry.has(DEVICE_RISK_TOOL_NAME) is True
    assert tool_registry.has("not_a_real_tool") is False


def test_registry_returns_callable_for_registered_tool():
    tool_fn = tool_registry.get(DEVICE_RISK_TOOL_NAME)

    assert callable(tool_fn)


def test_registry_unknown_tool_raises_clear_key_error():
    with pytest.raises(KeyError, match="Unknown tool"):
        tool_registry.get("not_a_real_tool")


def test_registry_rejects_duplicate_registration():
    registry = ToolRegistry()

    registry.register("dummy_tool", _dummy_tool)

    with pytest.raises(ValueError, match="Tool already registered"):
        registry.register("dummy_tool", _dummy_tool)


def test_registry_list_names_returns_sorted_names():
    registry = ToolRegistry()

    registry.register("z_tool", _dummy_tool)
    registry.register("a_tool", _dummy_tool)

    assert registry.list_names() == ["a_tool", "z_tool"]


def test_registry_all_returns_copy_not_internal_state():
    registry = ToolRegistry()

    registry.register("dummy_tool", _dummy_tool)

    tools_copy = registry.all()
    tools_copy["new_tool"] = _dummy_tool

    assert registry.has("dummy_tool") is True
    assert registry.has("new_tool") is False