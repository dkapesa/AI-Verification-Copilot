from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from eval_harness.schemas import SyntheticCase, VALID_DECISIONS


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


def load_raw_dataset() -> list[dict]:
    rows: list[dict] = []

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))

    return rows


def test_synthetic_dataset_exists() -> None:
    assert DATASET_PATH.exists()


def test_synthetic_dataset_loads_and_validates() -> None:
    rows = load_raw_dataset()
    cases = [SyntheticCase.model_validate(row) for row in rows]

    assert len(cases) >= 10
    assert {case.expected_decision for case in cases} == VALID_DECISIONS


def test_synthetic_dataset_has_unique_case_ids() -> None:
    rows = load_raw_dataset()
    cases = [SyntheticCase.model_validate(row) for row in rows]

    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))


def test_synthetic_case_rejects_invalid_decision() -> None:
    invalid_case = {
        "case_id": "case_invalid",
        "signals": {
            "device_risk": 0.2,
            "behaviour_anomaly": 0.2,
            "document_confidence": 0.9,
            "watchlist_match": False,
            "velocity_score": 0.1,
        },
        "expected_decision": "MANUAL_REVIEW",
        "outcome": {
            "fraud_confirmed": False,
            "manual_review_needed": False,
            "customer_harm_risk": "low",
        },
    }

    with pytest.raises(ValidationError):
        SyntheticCase.model_validate(invalid_case)


def test_synthetic_case_rejects_out_of_range_signal() -> None:
    invalid_case = {
        "case_id": "case_invalid",
        "signals": {
            "device_risk": 1.5,
            "behaviour_anomaly": 0.2,
            "document_confidence": 0.9,
            "watchlist_match": False,
            "velocity_score": 0.1,
        },
        "expected_decision": "APPROVE",
        "outcome": {
            "fraud_confirmed": False,
            "manual_review_needed": False,
            "customer_harm_risk": "low",
        },
    }

    with pytest.raises(ValidationError):
        SyntheticCase.model_validate(invalid_case)