from app.agents.schemas import AIReviewResponse, AggregatedSignal, DecisionOutput
from app.api.v1.endpoints import cases as cases_endpoint


def _create_case(client, payload: dict) -> dict:
    response = client.post("/api/v1/cases", json=payload)

    assert response.status_code == 200

    return response.json()


def _build_ai_review_response(
    *,
    case_id: str,
    decision: str,
    confidence: float,
    reasons: list[str],
    recommended_next_steps: list[str],
    overall_risk_score: float,
    high_risk_flags: list[str] | None = None,
    moderate_risk_flags: list[str] | None = None,
    low_risk_flags: list[str] | None = None,
) -> AIReviewResponse:
    return AIReviewResponse(
        case_id=case_id,
        status="COMPLETED",
        decision=DecisionOutput(
            decision=decision,
            confidence=confidence,
            reasons=reasons,
            recommended_next_steps=recommended_next_steps,
        ),
        aggregated_signals=AggregatedSignal(
            overall_risk_score=overall_risk_score,
            high_risk_flags=high_risk_flags or [],
            moderate_risk_flags=moderate_risk_flags or [],
            low_risk_flags=low_risk_flags or [],
            tool_summaries=[
                {
                    "tool_name": "device_risk_check",
                    "status": "SUCCESS",
                    "score": overall_risk_score,
                    "confidence": confidence,
                    "summary": f"Mocked {decision.lower()} scenario tool summary.",
                }
            ],
            tools_failed=[],
        ),
        tool_results_count=4,
        errors=[],
    )


def test_approve_workflow_scenario_with_mocked_ai_review(
    client,
    sample_case_payload,
    monkeypatch,
):
    approve_payload = {
        **sample_case_payload,
        "user_id": "approve_user_001",
        "email": "approve.user@example.com",
        "device_info": {
            **sample_case_payload["device_info"],
            "is_vpn": False,
            "is_emulator": False,
            "ip_country": "US",
        },
        "document_check_result": {
            **sample_case_payload["document_check_result"],
            "document_valid": True,
            "face_match_score": 0.98,
        },
        "behaviour_summary": {
            **sample_case_payload["behaviour_summary"],
            "failed_attempts": 0,
            "login_velocity": "normal",
        },
    }

    created_case = _create_case(client, approve_payload)

    async def fake_run_ai_review(*, db, case_id):
        return _build_ai_review_response(
            case_id=str(case_id),
            decision="APPROVE",
            confidence=0.94,
            reasons=[
                "Document checks passed and deterministic risk signals are low."
            ],
            recommended_next_steps=[
                "Approve verification and continue standard onboarding."
            ],
            overall_risk_score=0.18,
            low_risk_flags=["document_valid", "normal_login_velocity"],
        )

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{created_case['id']}/ai-review")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "COMPLETED"
    assert body["decision"]["decision"] == "APPROVE"
    assert body["decision"]["confidence"] == 0.94
    assert body["decision"]["reasons"] == [
        "Document checks passed and deterministic risk signals are low."
    ]
    assert body["decision"]["recommended_next_steps"] == [
        "Approve verification and continue standard onboarding."
    ]
    assert body["aggregated_signals"]["overall_risk_score"] == 0.18
    assert body["aggregated_signals"]["high_risk_flags"] == []
    assert body["aggregated_signals"]["low_risk_flags"] == [
        "document_valid",
        "normal_login_velocity",
    ]
    assert body["errors"] == []


def test_escalate_workflow_scenario_with_mocked_ai_review(
    client,
    sample_case_payload,
    monkeypatch,
):
    escalate_payload = {
        **sample_case_payload,
        "user_id": "escalate_user_001",
        "email": "escalate.user@example.com",
        "device_info": {
            **sample_case_payload["device_info"],
            "is_vpn": True,
            "is_emulator": False,
            "ip_country": "US",
        },
        "document_check_result": {
            **sample_case_payload["document_check_result"],
            "document_valid": True,
            "face_match_score": 0.83,
        },
        "behaviour_summary": {
            **sample_case_payload["behaviour_summary"],
            "failed_attempts": 3,
            "login_velocity": "elevated",
        },
    }

    created_case = _create_case(client, escalate_payload)

    async def fake_run_ai_review(*, db, case_id):
        return _build_ai_review_response(
            case_id=str(case_id),
            decision="ESCALATE",
            confidence=0.78,
            reasons=[
                "Moderate device and behaviour indicators require analyst review."
            ],
            recommended_next_steps=[
                "Escalate to fraud operations for manual verification."
            ],
            overall_risk_score=0.61,
            moderate_risk_flags=[
                "vpn_detected",
                "elevated_login_velocity",
                "face_match_review_recommended",
            ],
            low_risk_flags=["document_valid"],
        )

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{created_case['id']}/ai-review")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "COMPLETED"
    assert body["decision"]["decision"] == "ESCALATE"
    assert body["decision"]["confidence"] == 0.78
    assert body["decision"]["reasons"] == [
        "Moderate device and behaviour indicators require analyst review."
    ]
    assert body["decision"]["recommended_next_steps"] == [
        "Escalate to fraud operations for manual verification."
    ]
    assert body["aggregated_signals"]["overall_risk_score"] == 0.61
    assert body["aggregated_signals"]["moderate_risk_flags"] == [
        "vpn_detected",
        "elevated_login_velocity",
        "face_match_review_recommended",
    ]
    assert body["aggregated_signals"]["tools_failed"] == []
    assert body["errors"] == []


def test_reject_workflow_scenario_with_mocked_ai_review(
    client,
    sample_case_payload,
    monkeypatch,
):
    reject_payload = {
        **sample_case_payload,
        "user_id": "reject_user_001",
        "email": "reject.user@example.com",
        "device_info": {
            **sample_case_payload["device_info"],
            "is_vpn": True,
            "is_emulator": True,
            "ip_country": "high_risk_region",
        },
        "document_check_result": {
            **sample_case_payload["document_check_result"],
            "document_valid": False,
            "face_match_score": 0.41,
        },
        "behaviour_summary": {
            **sample_case_payload["behaviour_summary"],
            "failed_attempts": 8,
            "login_velocity": "high",
        },
    }

    created_case = _create_case(client, reject_payload)

    async def fake_run_ai_review(*, db, case_id):
        return _build_ai_review_response(
            case_id=str(case_id),
            decision="REJECT",
            confidence=0.91,
            reasons=[
                "High-risk device, document, and behaviour indicators were detected."
            ],
            recommended_next_steps=[
                "Reject verification and record fraud rationale in the audit trail."
            ],
            overall_risk_score=0.92,
            high_risk_flags=[
                "emulator_detected",
                "document_invalid",
                "high_login_velocity",
            ],
            moderate_risk_flags=["vpn_detected"],
        )

    monkeypatch.setattr(cases_endpoint, "run_ai_review", fake_run_ai_review)

    response = client.post(f"/api/v1/cases/{created_case['id']}/ai-review")

    assert response.status_code == 200

    body = response.json()

    assert body["case_id"] == created_case["id"]
    assert body["status"] == "COMPLETED"
    assert body["decision"]["decision"] == "REJECT"
    assert body["decision"]["confidence"] == 0.91
    assert body["decision"]["reasons"] == [
        "High-risk device, document, and behaviour indicators were detected."
    ]
    assert body["decision"]["recommended_next_steps"] == [
        "Reject verification and record fraud rationale in the audit trail."
    ]
    assert body["aggregated_signals"]["overall_risk_score"] == 0.92
    assert body["aggregated_signals"]["high_risk_flags"] == [
        "emulator_detected",
        "document_invalid",
        "high_login_velocity",
    ]
    assert body["aggregated_signals"]["moderate_risk_flags"] == ["vpn_detected"]
    assert body["errors"] == []