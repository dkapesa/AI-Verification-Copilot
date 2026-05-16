from uuid import uuid4


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200

    return response.json()


def test_get_audit_logs_returns_case_events(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    response = client.get(f"/api/v1/cases/{created_case['id']}/audit-logs")

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)
    assert len(body) >= 1

    first_event = body[0]

    assert "event_type" in first_event
    assert "actor_type" in first_event
    assert "created_at" in first_event


def test_case_creation_writes_case_created_audit_event(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    response = client.get(f"/api/v1/cases/{created_case['id']}/audit-logs")

    assert response.status_code == 200

    events = response.json()
    event_types = {event["event_type"] for event in events}

    assert "CASE_CREATED" in event_types


def test_case_view_writes_case_viewed_audit_event(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    get_response = client.get(f"/api/v1/cases/{created_case['id']}")

    assert get_response.status_code == 200

    audit_response = client.get(f"/api/v1/cases/{created_case['id']}/audit-logs")

    assert audit_response.status_code == 200

    events = audit_response.json()
    event_types = {event["event_type"] for event in events}

    assert "CASE_VIEWED" in event_types


def test_audit_logs_missing_case_returns_404(client):
    missing_case_id = uuid4()

    response = client.get(f"/api/v1/cases/{missing_case_id}/audit-logs")

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}