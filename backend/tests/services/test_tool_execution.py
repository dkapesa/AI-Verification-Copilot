import asyncio
from uuid import uuid4

from app.services import tool_runner
from app.services.tool_runner import run_tools_parallel
from app.tools.device_risk import TOOL_NAME as DEVICE_RISK_TOOL_NAME
from app.tools.registry import tool_registry
from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus


def _sample_tool_case_input() -> ToolCaseInput:
    return ToolCaseInput(
        case_id=uuid4(),
        user_id="user_test_001",
        email="test.user@example.com",
        device_info={
            "ip_country": "US",
            "device_fingerprint": "test-device-001",
            "is_vpn": False,
            "is_emulator": False,
        },
        document_check_result={
            "document_type": "passport",
            "document_country": "US",
            "document_valid": True,
            "face_match_score": 0.96,
        },
        behaviour_summary={
            "login_velocity": "normal",
            "failed_attempts": 0,
            "typing_pattern": "consistent",
        },
    )


def test_run_tools_parallel_executes_selected_registered_tool():
    case_input = _sample_tool_case_input()

    results = asyncio.run(
        run_tools_parallel(
            case_input=case_input,
            tool_names=[DEVICE_RISK_TOOL_NAME],
        )
    )

    assert len(results) == 1

    result = results[0]

    assert isinstance(result, ToolResult)
    assert result.tool_name == DEVICE_RISK_TOOL_NAME
    assert result.status in {status.value for status in ToolRunStatus}
    assert result.score is None or 0.0 <= result.score <= 1.0
    assert result.confidence is None or 0.0 <= result.confidence <= 1.0


def test_run_tools_parallel_executes_all_registered_tools():
    case_input = _sample_tool_case_input()
    registered_tool_names = set(tool_registry.list_names())

    results = asyncio.run(run_tools_parallel(case_input=case_input))

    result_tool_names = {result.tool_name for result in results}

    assert result_tool_names == registered_tool_names
    assert len(results) == len(registered_tool_names)

    for result in results:
        assert isinstance(result, ToolResult)
        assert result.status in {status.value for status in ToolRunStatus}
        assert result.score is None or 0.0 <= result.score <= 1.0
        assert result.confidence is None or 0.0 <= result.confidence <= 1.0


def test_run_tools_parallel_returns_empty_list_when_no_tools_requested():
    case_input = _sample_tool_case_input()

    results = asyncio.run(
        run_tools_parallel(
            case_input=case_input,
            tool_names=[],
        )
    )

    assert results == []


def test_run_tools_parallel_uses_all_tools_when_tool_names_is_none(monkeypatch):
    case_input = _sample_tool_case_input()

    async def success_tool_one(case_input: ToolCaseInput) -> ToolResult:
        return ToolResult(
            tool_name="success_tool_one",
            status=ToolRunStatus.SUCCESS,
            score=0.1,
            confidence=0.9,
            summary="Success tool one completed.",
        )

    async def success_tool_two(case_input: ToolCaseInput) -> ToolResult:
        return ToolResult(
            tool_name="success_tool_two",
            status=ToolRunStatus.SUCCESS,
            score=0.2,
            confidence=0.8,
            summary="Success tool two completed.",
        )

    class FakeRegistry:
        def list_names(self) -> list[str]:
            return ["success_tool_one", "success_tool_two"]

        def get(self, name: str):
            return {
                "success_tool_one": success_tool_one,
                "success_tool_two": success_tool_two,
            }[name]

    monkeypatch.setattr(tool_runner, "tool_registry", FakeRegistry())

    results = asyncio.run(run_tools_parallel(case_input=case_input))

    assert [result.tool_name for result in results] == [
        "success_tool_one",
        "success_tool_two",
    ]


def test_run_tools_parallel_does_not_block_successful_results_when_one_tool_fails(
    monkeypatch,
):
    case_input = _sample_tool_case_input()

    async def success_tool(case_input: ToolCaseInput) -> ToolResult:
        return ToolResult(
            tool_name="success_tool",
            status=ToolRunStatus.SUCCESS,
            score=0.2,
            confidence=0.9,
            summary="Successful tool completed.",
        )

    async def failing_tool(case_input: ToolCaseInput) -> ToolResult:
        raise RuntimeError("Simulated tool failure")

    class FakeRegistry:
        def get(self, name: str):
            return {
                "success_tool": success_tool,
                "failing_tool": failing_tool,
            }[name]

    monkeypatch.setattr(tool_runner, "tool_registry", FakeRegistry())

    results = asyncio.run(
        run_tools_parallel(
            case_input=case_input,
            tool_names=["success_tool", "failing_tool"],
        )
    )

    assert len(results) == 1
    assert results[0].tool_name == "success_tool"
    assert results[0].status == ToolRunStatus.SUCCESS