from __future__ import annotations

import csv
import json
import time
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from eval_harness.environment import (
    DEFAULT_DATASET_PATH,
    VerificationFeedbackEnvironment,
)
from eval_harness.metrics import summarize_results
from eval_harness.run_experiment import DEFAULT_OUTPUT_DIR
from eval_harness.schemas import DecisionAction, EvaluationStepResult


DEFAULT_SAVED_AI_REVIEW_INPUT_PATH = (
    Path("experiments") / "saved_ai_review_examples.jsonl"
)


def _json_safe(value: Any) -> Any:
    """Convert nested payload values into JSON-serializable objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Enum):
        return _json_safe(value.value)

    if hasattr(value, "value") and isinstance(
        value.value,
        (str, int, float, bool),
    ):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump())

    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    return str(value)


class SavedAIReviewRecord(BaseModel):
    """
    A saved structured AI review output for offline evaluation.

    This fixture represents a previously generated AI review decision. It does
    not call a live model provider and should only be used with synthetic
    expected outcomes.
    """

    case_id: str = Field(..., min_length=1)
    expected_decision: DecisionAction | None = None
    saved_decision: DecisionAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def load_saved_ai_review_records(
    path: Path | str = DEFAULT_SAVED_AI_REVIEW_INPUT_PATH,
) -> list[SavedAIReviewRecord]:
    """
    Load saved AI review outputs from a JSONL fixture.

    Each non-empty line must contain one saved structured AI decision. Validation
    is strict so malformed fixtures fail clearly before evaluation starts.
    """
    input_path = Path(path)

    if not input_path.exists():
        raise FileNotFoundError(f"Saved AI review fixture not found: {input_path}")

    records: list[SavedAIReviewRecord] = []

    with input_path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()

            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in saved AI review fixture on line {line_number}: {exc}"
                ) from exc

            try:
                records.append(SavedAIReviewRecord.model_validate(payload))
            except ValidationError as exc:
                raise ValueError(
                    "Invalid saved AI review record "
                    f"on line {line_number}: {exc}"
                ) from exc

    if not records:
        raise ValueError("Saved AI review fixture must contain at least one record.")

    return records


def _build_output_filename(*, generated_at: datetime) -> str:
    timestamp = generated_at.strftime("%Y-%m-%d-%H%M%S")
    return f"{timestamp}-saved-ai-review-evaluation"


def _write_json_result(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(_json_safe(payload), file, indent=2, sort_keys=True)


def _write_csv_records(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row",
        "case_id",
        "decision",
        "expected_decision",
        "reward",
        "correct",
        "reward_reason",
        "saved_review_confidence",
        "saved_review_reasons",
        "error",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            metadata = record.get("metadata", {})
            writer.writerow(
                {
                    "row": record["row"],
                    "case_id": record["case_id"],
                    "decision": record["decision"],
                    "expected_decision": record["expected_decision"],
                    "reward": record["reward"],
                    "correct": record["correct"],
                    "reward_reason": metadata.get("reward_reason"),
                    "saved_review_confidence": record.get("saved_review_confidence"),
                    "saved_review_reasons": " | ".join(
                        record.get("saved_review_reasons") or []
                    ),
                    "error": metadata.get("error"),
                }
            )


def evaluate_saved_ai_reviews(
    *,
    input_path: Path | str = DEFAULT_SAVED_AI_REVIEW_INPUT_PATH,
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    write_files: bool = True,
) -> dict:
    """
    Evaluate saved structured AI review decisions against synthetic cases.

    This is an offline evaluator. It does not call OpenAI, Ollama, LangGraph, or
    any external provider. It maps saved review decisions onto the existing
    synthetic verification environment and reuses the existing reward/metrics
    path.
    """
    saved_reviews = load_saved_ai_review_records(input_path)
    environment = VerificationFeedbackEnvironment.from_jsonl(dataset_path)

    started_at = time.perf_counter()
    results: list[EvaluationStepResult] = []
    decision_records: list[dict] = []
    failure_count = 0

    for row_number, saved_review in enumerate(saved_reviews, start=1):
        try:
            synthetic_case = environment.get_case(saved_review.case_id)

            if (
                saved_review.expected_decision is not None
                and saved_review.expected_decision != synthetic_case.expected_decision
            ):
                raise ValueError(
                    "Saved review expected_decision does not match dataset "
                    f"for case_id={saved_review.case_id}: "
                    f"fixture={saved_review.expected_decision}, "
                    f"dataset={synthetic_case.expected_decision}"
                )

            step_result = environment.step(
                saved_review.case_id,
                saved_review.saved_decision,
            )

            enriched_metadata = {
                **step_result.metadata,
                "saved_review_confidence": saved_review.confidence,
                "saved_review_reasons": saved_review.reasons,
                "saved_review_metadata": saved_review.metadata,
                "fixture_expected_decision": saved_review.expected_decision,
            }

            enriched_result = step_result.model_copy(
                update={"metadata": enriched_metadata}
            )
            results.append(enriched_result)

            decision_records.append(
                {
                    "row": row_number,
                    "case_id": enriched_result.case_id,
                    "decision": enriched_result.decision,
                    "expected_decision": enriched_result.expected_decision,
                    "reward": enriched_result.reward,
                    "correct": enriched_result.correct,
                    "outcome": _json_safe(enriched_result.outcome),
                    "metadata": enriched_result.metadata,
                    "saved_review_confidence": saved_review.confidence,
                    "saved_review_reasons": saved_review.reasons,
                }
            )

        except Exception as exc:
            failure_count += 1
            decision_records.append(
                {
                    "row": row_number,
                    "case_id": saved_review.case_id,
                    "decision": saved_review.saved_decision,
                    "expected_decision": saved_review.expected_decision,
                    "reward": None,
                    "correct": False,
                    "outcome": None,
                    "metadata": {"error": str(exc)},
                    "saved_review_confidence": saved_review.confidence,
                    "saved_review_reasons": saved_review.reasons,
                }
            )

    runtime_seconds = time.perf_counter() - started_at

    metrics = summarize_results(
        results,
        failure_count=failure_count,
        runtime_seconds=runtime_seconds,
    )

    generated_at = datetime.now(timezone.utc)
    output_dir_path = Path(output_dir)
    base_filename = _build_output_filename(generated_at=generated_at)

    json_output_path = output_dir_path / f"{base_filename}.json"
    csv_output_path = output_dir_path / f"{base_filename}.csv"

    payload = {
        "experiment_type": "saved_ai_review_output_evaluation",
        "generated_at": generated_at.isoformat(),
        "input_path": str(input_path),
        "dataset_path": str(dataset_path),
        "metrics": metrics,
        "decision_records": decision_records,
        "output_files": {
            "json": str(json_output_path),
            "csv": str(csv_output_path),
        },
        "limitations": [
            "Synthetic expected outcomes only.",
            "No real fraud labels are used.",
            "Saved AI review decisions are evaluated offline without live model calls.",
            "Metrics describe saved structured decision behaviour only and should not be interpreted as production fraud-model performance.",
        ],
    }

    if write_files:
        _write_json_result(payload, json_output_path)
        _write_csv_records(decision_records, csv_output_path)

    return payload
