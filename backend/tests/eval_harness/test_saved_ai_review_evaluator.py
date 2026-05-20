from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_harness.environment import (
    DEFAULT_DATASET_PATH,
    VerificationFeedbackEnvironment,
)
from eval_harness.saved_ai_review_evaluator import (
    evaluate_saved_ai_reviews,
    load_saved_ai_review_records,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _environment() -> VerificationFeedbackEnvironment:
    return VerificationFeedbackEnvironment.from_jsonl(DEFAULT_DATASET_PATH)


def _first_case_with_expected_not(decision: str):
    for case in _environment().cases:
        if case.expected_decision != decision:
            return case

    raise AssertionError(f"Test dataset needs at least one case not expected as {decision}.")


def _first_case() -> object:
    return _environment().cases[0]


def test_load_saved_ai_review_records_validates_fixture(tmp_path: Path) -> None:
    case = _first_case()
    fixture_path = tmp_path / "saved_reviews.jsonl"

    _write_jsonl(
        fixture_path,
        [
            {
                "case_id": case.case_id,
                "expected_decision": case.expected_decision,
                "saved_decision": case.expected_decision,
                "confidence": 0.91,
                "reasons": ["Synthetic saved review matched expected decision."],
                "metadata": {"source": "pytest"},
            }
        ],
    )

    records = load_saved_ai_review_records(fixture_path)

    assert len(records) == 1
    assert records[0].case_id == case.case_id
    assert records[0].saved_decision == case.expected_decision
    assert records[0].confidence == 0.91
    assert records[0].metadata["source"] == "pytest"


def test_load_saved_ai_review_records_rejects_missing_decision(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "invalid_saved_reviews.jsonl"

    _write_jsonl(
        fixture_path,
        [
            {
                "case_id": "synthetic-case",
                "expected_decision": "APPROVE",
                "confidence": 0.75,
                "reasons": ["Missing saved_decision should fail validation."],
            }
        ],
    )

    with pytest.raises(ValueError, match="Invalid saved AI review record"):
        load_saved_ai_review_records(fixture_path)


def test_evaluate_saved_ai_reviews_calculates_core_metrics(
    tmp_path: Path,
) -> None:
    correct_case = _first_case()
    false_approve_case = _first_case_with_expected_not("APPROVE")
    false_reject_case = _first_case_with_expected_not("REJECT")
    escalation_case = _first_case_with_expected_not("ESCALATE")

    fixture_path = tmp_path / "saved_reviews.jsonl"

    _write_jsonl(
        fixture_path,
        [
            {
                "case_id": correct_case.case_id,
                "expected_decision": correct_case.expected_decision,
                "saved_decision": correct_case.expected_decision,
                "confidence": 0.92,
                "reasons": ["Saved review matched the synthetic expected outcome."],
                "metadata": {"scenario": "correct"},
            },
            {
                "case_id": false_approve_case.case_id,
                "expected_decision": false_approve_case.expected_decision,
                "saved_decision": "APPROVE",
                "confidence": 0.84,
                "reasons": ["Saved review approved a non-approve synthetic case."],
                "metadata": {"scenario": "false_approve"},
            },
            {
                "case_id": false_reject_case.case_id,
                "expected_decision": false_reject_case.expected_decision,
                "saved_decision": "REJECT",
                "confidence": 0.79,
                "reasons": ["Saved review rejected a non-reject synthetic case."],
                "metadata": {"scenario": "false_reject"},
            },
            {
                "case_id": escalation_case.case_id,
                "expected_decision": escalation_case.expected_decision,
                "saved_decision": "ESCALATE",
                "confidence": 0.67,
                "reasons": ["Saved review escalated an uncertain synthetic case."],
                "metadata": {"scenario": "escalation"},
            },
        ],
    )

    payload = evaluate_saved_ai_reviews(
        input_path=fixture_path,
        dataset_path=DEFAULT_DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    metrics = payload["metrics"]

    assert payload["experiment_type"] == "saved_ai_review_output_evaluation"
    assert metrics["total_cases"] == 4
    assert metrics["failure_count"] == 0
    assert metrics["false_approve_count"] == 1
    assert metrics["false_reject_count"] == 1
    assert metrics["escalation_count"] == 1
    assert metrics["decision_distribution"]["APPROVE"] >= 1
    assert metrics["decision_distribution"]["ESCALATE"] == 1
    assert metrics["decision_distribution"]["REJECT"] >= 1
    assert len(payload["decision_records"]) == 4


def test_evaluate_saved_ai_reviews_counts_missing_case_as_failure(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "saved_reviews_with_missing_case.jsonl"

    _write_jsonl(
        fixture_path,
        [
            {
                "case_id": "missing-synthetic-case-id",
                "expected_decision": "APPROVE",
                "saved_decision": "APPROVE",
                "confidence": 0.88,
                "reasons": ["This case ID should not exist in the dataset."],
                "metadata": {"scenario": "missing_case"},
            }
        ],
    )

    payload = evaluate_saved_ai_reviews(
        input_path=fixture_path,
        dataset_path=DEFAULT_DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    assert payload["metrics"]["total_cases"] == 0
    assert payload["metrics"]["failure_count"] == 1
    assert "Unknown synthetic case_id" in payload["decision_records"][0]["metadata"]["error"]


def test_evaluate_saved_ai_reviews_writes_json_and_csv_outputs(
    tmp_path: Path,
) -> None:
    case = _first_case()
    fixture_path = tmp_path / "saved_reviews.jsonl"

    _write_jsonl(
        fixture_path,
        [
            {
                "case_id": case.case_id,
                "expected_decision": case.expected_decision,
                "saved_decision": case.expected_decision,
                "confidence": 0.9,
                "reasons": ["Saved review matched expected decision."],
                "metadata": {"scenario": "file_output"},
            }
        ],
    )

    payload = evaluate_saved_ai_reviews(
        input_path=fixture_path,
        dataset_path=DEFAULT_DATASET_PATH,
        output_dir=tmp_path,
        write_files=True,
    )

    assert Path(payload["output_files"]["json"]).exists()
    assert Path(payload["output_files"]["csv"]).exists()
