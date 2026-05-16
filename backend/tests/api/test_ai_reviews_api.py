from uuid import UUID, uuid4

from app.agents.schemas import AIReviewResponse, AggregatedSignal, DecisionOutput
from app.api.v1.endpoints import cases as cases_endpoint
from app.crud.ai_review import create_ai_review


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200

    return response.json()


def _aggregated_signals_payload() -> dict:
    return {
        "overall_risk_score": 0.42,
        "high_risk_flags": [],
        "moderate_risk_flags": ["device_velocity_moderate"],
        "low_risk_flags": ["document_valid"],
        "tool_summaries": [
            {
                "tool_name": "device_risk_check",
                "status": "SUCCESS",
                "score": 0.35,
                "confidence": 0.91,
                "summary": "No high-risk device indicators found.",
            }
        ],
        "tools_failed": [],
    }


def test_ai_review_endpoint_returns_mocked_structured_response(
    client,
    sample_case_payload,
    monkeypatch,
):
    created_case = _create_case(client, sample_case_payload)

    async def fake_run_ai_review(*, db, case_id):
        return AIReviewResponse(
            case_id=str(case_id),
            status="COMPLETED",
            decision=DecisionOutput(
                decision="ESCALATE",
                confidence=0.77,
                reasons=["Moderate risk indicators require analyst review."],
                recommended_next_steps=["Route to fraud operations queue."],
            ),
            aggregated_signals=AggregatedSignal(**_aggregated_signals_payload()),
            tool_results_count=4,
            errors=[],
        )

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{created_case['id']}/ai-review")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "COMPLETED"
    assert body["decision"]["decision"] == "ESCALATE"
    assert body["decision"]["confidence"] == 0.77
    assert body["decision"]["reasons"] == [
        "Moderate risk indicators require analyst review."
    ]
    assert body["decision"]["recommended_next_steps"] == [
        "Route to fraud operations queue."
    ]
    assert body["aggregated_signals"]["overall_risk_score"] == 0.42
    assert body["tool_results_count"] == 4
    assert body["errors"] == []


def test_ai_review_endpoint_can_return_mocked_failed_response(
    client,
    sample_case_payload,
    monkeypatch,
):
    created_case = _create_case(client, sample_case_payload)

    async def fake_run_ai_review(*, db, case_id):
        return AIReviewResponse(
            case_id=str(case_id),
            status="FAILED",
            decision=None,
            aggregated_signals=None,
            tool_results_count=0,
            errors=["AI review failed after retries."],
        )

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{created_case['id']}/ai-review")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "FAILED"
    assert body["decision"] is None
    assert body["aggregated_signals"] is None
    assert body["tool_results_count"] == 0
    assert body["errors"] == ["AI review failed after retries."]


def test_ai_review_missing_case_returns_404_without_running_ai_review(
    client,
    monkeypatch,
):
    missing_case_id = uuid4()
    called = {"value": False}

    async def fake_run_ai_review(*, db, case_id):
        called["value"] = True
        raise AssertionError("run_ai_review should not be called for a missing case")

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{missing_case_id}/ai-review")

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}
    assert called["value"] is False


def test_get_latest_ai_review_returns_persisted_review(
    client,
    db_session,
    sample_case_payload,
):
    created_case = _create_case(client, sample_case_payload)
    case_id = UUID(created_case["id"])

    create_ai_review(
        db=db_session,
        case_id=case_id,
        decision="APPROVE",
        confidence=0.93,
        reasons=["All deterministic signals were low risk."],
        recommended_next_steps=["Approve verification."],
        aggregated_signals=_aggregated_signals_payload(),
        reasoning_summary="Overall risk score=0.42; high=0; moderate=1; low=1; failed_tools=0",
        model_provider="test",
        model_name="mock-model",
        prompt_version="test-v1",
        retry_count=0,
        latency_ms=123,
    )

    response = client.get(f"/api/v1/cases/{created_case['id']}/ai-reviews/latest")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "COMPLETED"
    assert body["decision"]["decision"] == "APPROVE"
    assert body["decision"]["confidence"] == 0.93
    assert body["decision"]["reasons"] == [
        "All deterministic signals were low risk."
    ]
    assert body["decision"]["recommended_next_steps"] == [
        "Approve verification."
    ]
    assert body["aggregated_signals"]["overall_risk_score"] == 0.42
    assert body["tool_results_count"] == 1
    assert body["errors"] == []


def test_get_latest_ai_review_missing_review_returns_404(
    client,
    sample_case_payload,
):
    created_case = _create_case(client, sample_case_payload)

    response = client.get(f"/api/v1/cases/{created_case['id']}/ai-reviews/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "No AI review found for case"}


def test_get_latest_ai_review_missing_case_returns_404(client):
    missing_case_id = uuid4()

    response = client.get(f"/api/v1/cases/{missing_case_id}/ai-reviews/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}