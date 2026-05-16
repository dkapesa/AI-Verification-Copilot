from uuid import UUID, uuid4

from app.crud.ai_review import create_ai_review


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200

    body = response.json()
    UUID(body["id"])

    return body


def test_create_human_override_returns_persisted_override(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    payload = {
        "decision": "ESCALATE",
        "reason": "Manual reviewer found signals that require additional checks.",
    }

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert UUID(body["id"])
    assert body["case_id"] == created_case["id"]
    assert body["decision"] == "ESCALATE"
    assert body["reason"] == payload["reason"]
    assert body["actor_type"] == "human"
    assert body["original_ai_decision"] is None
    assert body["created_at"] is not None


def test_create_human_override_requires_reason(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    payload = {
        "decision": "ESCALATE",
    }

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=payload,
    )

    assert response.status_code == 422


def test_create_human_override_rejects_invalid_decision(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    payload = {
        "decision": "MANUAL_REVIEW",
        "reason": "This decision label is not supported.",
    }

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=payload,
    )

    assert response.status_code == 422


def test_create_human_override_missing_case_returns_404(client):
    missing_case_id = uuid4()

    payload = {
        "decision": "REJECT",
        "reason": "Manual reviewer found clear fraud indicators.",
    }

    response = client.post(
        f"/api/v1/cases/{missing_case_id}/human-override",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_get_latest_human_override_returns_latest_override(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    first_payload = {
        "decision": "ESCALATE",
        "reason": "Initial manual review requires more evidence.",
    }

    second_payload = {
        "decision": "REJECT",
        "reason": "Follow-up review confirmed fraud indicators.",
    }

    first_response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=first_payload,
    )
    second_response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=second_payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    response = client.get(
        f"/api/v1/cases/{created_case['id']}/human-overrides/latest"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["decision"] == "REJECT"
    assert body["reason"] == second_payload["reason"]


def test_get_latest_human_override_missing_override_returns_404(
    client,
    sample_case_payload,
):
    created_case = _create_case(client, sample_case_payload)

    response = client.get(
        f"/api/v1/cases/{created_case['id']}/human-overrides/latest"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No human override found for case"}


def test_get_latest_human_override_missing_case_returns_404(client):
    missing_case_id = uuid4()

    response = client.get(
        f"/api/v1/cases/{missing_case_id}/human-overrides/latest"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_create_human_override_writes_audit_event(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    payload = {
        "decision": "APPROVE",
        "reason": "Manual reviewer confirmed the case is low risk.",
    }

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=payload,
    )

    assert response.status_code == 200

    audit_response = client.get(f"/api/v1/cases/{created_case['id']}/audit-logs")

    assert audit_response.status_code == 200

    events = audit_response.json()
    override_events = [
        event
        for event in events
        if event["event_type"] == "HUMAN_OVERRIDE_CREATED"
    ]

    assert len(override_events) == 1

    event = override_events[0]

    assert event["actor_type"] == "human"
    assert event["subject"] == "human_override"
    assert event["meta"]["decision"] == "APPROVE"
    assert event["meta"]["reason_length"] == len(payload["reason"])
    assert "override_id" in event["meta"]


def test_create_human_override_captures_original_ai_decision(
    client,
    db_session,
    sample_case_payload,
):
    created_case = _create_case(client, sample_case_payload)
    case_id = UUID(created_case["id"])

    create_ai_review(
        db=db_session,
        case_id=case_id,
        decision="ESCALATE",
        confidence=0.72,
        reasons=["Synthetic mocked reason for persistence test."],
        recommended_next_steps=["Manual review required."],
        aggregated_signals={
            "overall_risk_score": 0.65,
            "high_risk_flags": [],
            "moderate_risk_flags": ["manual_review_needed"],
            "low_risk_flags": [],
            "tool_summaries": [],
        },
        reasoning_summary="Mocked AI review summary.",
        model_provider="test",
        model_name="mock-model",
        prompt_version="test-v1",
        retry_count=0,
        latency_ms=10,
    )

    payload = {
        "decision": "REJECT",
        "reason": "Human reviewer overrode the AI escalation after further checks.",
    }

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/human-override",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["decision"] == "REJECT"
    assert body["original_ai_decision"] == "ESCALATE"