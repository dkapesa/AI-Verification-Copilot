from uuid import uuid4


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200

    return response.json()


def test_run_tools_returns_structured_results(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/run-tools",
        json={},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert "results" in body
    assert isinstance(body["results"], list)
    assert len(body["results"]) >= 1

    first_result = body["results"][0]

    assert "tool_name" in first_result
    assert "status" in first_result
    assert "score" in first_result
    assert "confidence" in first_result
    assert "summary" in first_result


def test_run_tools_persists_latest_tool_results(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    run_response = client.post(
        f"/api/v1/cases/{created_case['id']}/run-tools",
        json={},
    )

    assert run_response.status_code == 200

    latest_response = client.get(
        f"/api/v1/cases/{created_case['id']}/tool-runs"
    )

    assert latest_response.status_code == 200

    run_body = run_response.json()
    latest_body = latest_response.json()

    assert latest_body["case_id"] == created_case["id"]
    assert "results" in latest_body
    assert isinstance(latest_body["results"], list)
    assert len(latest_body["results"]) == len(run_body["results"])

    run_tool_names = {result["tool_name"] for result in run_body["results"]}
    latest_tool_names = {result["tool_name"] for result in latest_body["results"]}

    assert latest_tool_names == run_tool_names


def test_run_tools_rejects_unknown_tool_name(client, sample_case_payload):
    created_case = _create_case(client, sample_case_payload)

    response = client.post(
        f"/api/v1/cases/{created_case['id']}/run-tools",
        json={"tool_names": ["not_a_real_tool"]},
    )

    assert response.status_code == 400
    assert "Unknown tool names" in response.json()["detail"]


def test_run_tools_missing_case_returns_404(client):
    missing_case_id = uuid4()

    response = client.post(
        f"/api/v1/cases/{missing_case_id}/run-tools",
        json={},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_get_tool_runs_missing_case_returns_404(client):
    missing_case_id = uuid4()

    response = client.get(f"/api/v1/cases/{missing_case_id}/tool-runs")

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}