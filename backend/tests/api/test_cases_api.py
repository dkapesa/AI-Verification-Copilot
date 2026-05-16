from uuid import UUID, uuid4


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    UUID(body["id"])

    return body


def test_create_case_returns_persisted_case(client, sample_case_payload):
    body = _create_case(client, sample_case_payload)

    assert body["user_id"] == sample_case_payload["user_id"]
    assert body["email"] == sample_case_payload["email"]
    assert body["status"] == "PENDING"

    assert body["device_info"] == sample_case_payload["device_info"]
    assert body["document_check_result"] == sample_case_payload["document_check_result"]
    assert body["behaviour_summary"] == sample_case_payload["behaviour_summary"]

    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_get_case_by_id_returns_case(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    response = client.get(f"/api/v1/cases/{created_case['id']}")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created_case["id"]
    assert body["user_id"] == sample_case_payload["user_id"]
    assert body["email"] == sample_case_payload["email"]
    assert body["status"] == "PENDING"


def test_get_missing_case_returns_structured_404(client):
    missing_case_id = uuid4()

    response = client.get(f"/api/v1/cases/{missing_case_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_list_cases_supports_pagination(client, sample_case_payload):
    for index in range(3):
        payload = {
            **sample_case_payload,
            "user_id": f"user_test_{index}",
            "email": f"test.user.{index}@example.com",
        }
        _create_case(client, payload)

    response = client.get("/api/v1/cases?limit=2&offset=0")

    assert response.status_code == 200

    body = response.json()

    assert body["limit"] == 2
    assert body["offset"] == 0
    assert body["total"] >= 3
    assert len(body["items"]) == 2

    for item in body["items"]:
        assert "id" in item
        assert "user_id" in item
        assert "email" in item
        assert "status" in item
        assert "created_at" in item
        assert "updated_at" in item


def test_list_cases_second_page_uses_offset(client, sample_case_payload):
    created_ids = []

    for index in range(3):
        payload = {
            **sample_case_payload,
            "user_id": f"offset_user_test_{index}",
            "email": f"offset.user.{index}@example.com",
        }
        created = _create_case(client, payload)
        created_ids.append(created["id"])

    first_page_response = client.get("/api/v1/cases?limit=2&offset=0")
    second_page_response = client.get("/api/v1/cases?limit=2&offset=2")

    assert first_page_response.status_code == 200
    assert second_page_response.status_code == 200

    first_page_ids = {item["id"] for item in first_page_response.json()["items"]}
    second_page_ids = {item["id"] for item in second_page_response.json()["items"]}

    assert first_page_ids
    assert second_page_ids
    assert first_page_ids.isdisjoint(second_page_ids)