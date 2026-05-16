from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_harness.run_experiment import run_experiment


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


def test_run_experiment_returns_expected_payload_fields(tmp_path: Path) -> None:
    payload = run_experiment(
        policy_name="rules",
        episodes=10,
        seed=42,
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    assert payload["experiment_name"] == "learning_from_feedback_evaluation_harness"
    assert payload["policy_name"] == "rules"
    assert payload["episodes"] == 10
    assert payload["seed"] == 42
    assert payload["metrics"]["total_cases"] == 10
    assert "accuracy" in payload["metrics"]
    assert "average_reward" in payload["metrics"]
    assert "false_approve_rate" in payload["metrics"]
    assert "false_reject_rate" in payload["metrics"]
    assert "escalation_rate" in payload["metrics"]
    assert "decision_distribution" in payload["metrics"]
    assert len(payload["decision_records"]) == 10


def test_run_experiment_writes_json_and_csv_files(tmp_path: Path) -> None:
    payload = run_experiment(
        policy_name="rules",
        episodes=5,
        seed=7,
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=True,
    )

    json_path = Path(payload["output_files"]["json"])
    csv_path = Path(payload["output_files"]["csv"])

    assert json_path.exists()
    assert csv_path.exists()

    with json_path.open("r", encoding="utf-8") as file:
        saved_payload = json.load(file)

    assert saved_payload["policy_name"] == "rules"
    assert saved_payload["episodes"] == 5
    assert saved_payload["metrics"]["total_cases"] == 5


def test_run_experiment_is_reproducible_for_same_seed(tmp_path: Path) -> None:
    first = run_experiment(
        policy_name="rules",
        episodes=20,
        seed=123,
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    second = run_experiment(
        policy_name="rules",
        episodes=20,
        seed=123,
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    first_records = [
        {
            "episode": record["episode"],
            "case_id": record["case_id"],
            "decision": record["decision"],
            "expected_decision": record["expected_decision"],
            "reward": record["reward"],
            "correct": record["correct"],
        }
        for record in first["decision_records"]
    ]

    second_records = [
        {
            "episode": record["episode"],
            "case_id": record["case_id"],
            "decision": record["decision"],
            "expected_decision": record["expected_decision"],
            "reward": record["reward"],
            "correct": record["correct"],
        }
        for record in second["decision_records"]
    ]

    assert first_records == second_records
    assert first["metrics"]["accuracy"] == second["metrics"]["accuracy"]
    assert first["metrics"]["average_reward"] == second["metrics"]["average_reward"]


def test_feedback_adjusted_experiment_records_policy_state(tmp_path: Path) -> None:
    payload = run_experiment(
        policy_name="feedback_adjusted",
        episodes=25,
        seed=42,
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    policy_state = payload["feedback_policy_state"]

    assert policy_state is not None
    assert "approve_threshold" in policy_state
    assert "reject_threshold" in policy_state
    assert "history_length" in policy_state
    assert policy_state["history_length"] == 25


def test_run_experiment_rejects_invalid_episode_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_experiment(
            policy_name="rules",
            episodes=0,
            seed=42,
            dataset_path=DATASET_PATH,
            output_dir=tmp_path,
            write_files=False,
        )