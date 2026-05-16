from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.tools.schemas import ToolCaseInput, ToolResult
from app.tools.types import ToolRunStatus


def _valid_tool_status() -> ToolRunStatus:
    return list(ToolRunStatus)[0]


def test_valid_tool_case_input_schema_passes():
    payload = ToolCaseInput(
        case_id=uuid4(),
        user_id="user_test_001",
        email="test.user@example.com",
        device_info={"ip_country": "US", "is_vpn": False},
        document_check_result={"document_valid": True},
        behaviour_summary={"failed_attempts": 0},
    )

    assert payload.user_id == "user_test_001"
    assert payload.email == "test.user@example.com"
    assert payload.device_info["ip_country"] == "US"


def test_tool_case_input_rejects_invalid_email():
    with pytest.raises(ValidationError):
        ToolCaseInput(
            case_id=uuid4(),
            user_id="user_test_001",
            email="not-an-email",
            device_info={},
            document_check_result={},
            behaviour_summary={},
        )


def test_valid_tool_result_schema_passes():
    result = ToolResult(
        tool_name="device_risk_check",
        status=_valid_tool_status(),
        score=0.72,
        confidence=0.91,
        summary="Device risk check completed.",
        signals={"vpn_detected": False},
        output={"risk_level": "moderate"},
        latency_ms=42,
    )

    assert result.tool_name == "device_risk_check"
    assert result.score == 0.72
    assert result.confidence == 0.91
    assert result.signals["vpn_detected"] is False
    assert result.output["risk_level"] == "moderate"
    assert result.latency_ms == 42


def test_tool_result_rejects_invalid_status():
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="device_risk_check",
            status="NOT_A_REAL_STATUS",
            score=0.5,
            confidence=0.8,
        )


def test_tool_result_rejects_score_below_zero():
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="rules_risk_score",
            status=_valid_tool_status(),
            score=-0.01,
            confidence=0.8,
        )


def test_tool_result_rejects_score_above_one():
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="rules_risk_score",
            status=_valid_tool_status(),
            score=1.01,
            confidence=0.8,
        )


def test_tool_result_rejects_confidence_below_zero():
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="watchlist_screening",
            status=_valid_tool_status(),
            score=0.4,
            confidence=-0.01,
        )


def test_tool_result_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="watchlist_screening",
            status=_valid_tool_status(),
            score=0.4,
            confidence=1.01,
        )


def test_tool_result_allows_nested_signals_and_output():
    result = ToolResult(
        tool_name="behaviour_anomaly_check",
        status=_valid_tool_status(),
        score=0.61,
        confidence=0.88,
        summary="Behaviour anomaly check completed.",
        signals={
            "velocity": {
                "login_count_24h": 3,
                "risk": "low",
            }
        },
        output={
            "checks": [
                {"name": "failed_attempts", "passed": True},
                {"name": "typing_pattern", "passed": True},
            ]
        },
    )

    assert result.signals["velocity"]["login_count_24h"] == 3
    assert result.output["checks"][0]["name"] == "failed_attempts"