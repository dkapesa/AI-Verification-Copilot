from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from eval_harness.run_multi_seed_experiment import run_multi_seed_experiment


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "eval_harness"
    / "data"
    / "synthetic_cases.jsonl"
)


def test_multi_seed_experiment_returns_expected_payload_fields(tmp_path: Path) -> None:
    payload = run_multi_seed_experiment(
        episodes=6,
        seeds=[1, 7],
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    assert payload["experiment_type"] == "multi_seed_policy_comparison"
    assert payload["dataset"] == "synthetic_cases.jsonl"
    assert payload["episodes_per_seed"] == 6
    assert payload["seeds"] == [1, 7]
    assert payload["policies"] == ["rules", "ai_review", "feedback_adjusted"]

    assert len(payload["runs"]) == 6

    for run in payload["runs"]:
        assert run["policy"] in {"rules", "ai_review", "feedback_adjusted"}
        assert run["seed"] in {1, 7}
        assert run["episodes"] == 6
        assert run["metrics"]["total_cases"] == 6
        assert "accuracy" in run["metrics"]
        assert "average_reward" in run["metrics"]
        assert "false_approve_rate" in run["metrics"]
        assert "false_reject_rate" in run["metrics"]
        assert "escalation_rate" in run["metrics"]


def test_multi_seed_experiment_aggregates_all_policies(tmp_path: Path) -> None:
    payload = run_multi_seed_experiment(
        episodes=8,
        seeds=[1, 7],
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    aggregate_metrics = payload["aggregate_metrics"]

    assert set(aggregate_metrics.keys()) == {
        "rules",
        "ai_review",
        "feedback_adjusted",
    }

    for policy_name in ["rules", "ai_review", "feedback_adjusted"]:
        policy_metrics = aggregate_metrics[policy_name]

        assert policy_metrics["run_count"] == 2
        assert policy_metrics["total_evaluated_cases"] == 16
        assert "accuracy_mean" in policy_metrics
        assert "accuracy_std" in policy_metrics
        assert "average_reward_mean" in policy_metrics
        assert "average_reward_std" in policy_metrics
        assert "false_approve_rate_mean" in policy_metrics
        assert "false_approve_rate_std" in policy_metrics
        assert "false_reject_rate_mean" in policy_metrics
        assert "false_reject_rate_std" in policy_metrics
        assert "escalation_rate_mean" in policy_metrics
        assert "escalation_rate_std" in policy_metrics
        assert "failure_count_total" in policy_metrics
        assert "decision_distribution_summary" in policy_metrics


def test_multi_seed_experiment_decision_distribution_summary(tmp_path: Path) -> None:
    payload = run_multi_seed_experiment(
        episodes=5,
        seeds=[1, 7],
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    for policy_metrics in payload["aggregate_metrics"].values():
        distribution_summary = policy_metrics["decision_distribution_summary"]

        assert set(distribution_summary.keys()) == {"total", "mean_rate"}
        assert set(distribution_summary["total"].keys()) == {
            "APPROVE",
            "ESCALATE",
            "REJECT",
        }
        assert set(distribution_summary["mean_rate"].keys()) == {
            "APPROVE",
            "ESCALATE",
            "REJECT",
        }


def test_multi_seed_experiment_writes_json_and_csv_files(tmp_path: Path) -> None:
    payload = run_multi_seed_experiment(
        episodes=5,
        seeds=[1, 7],
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

    assert saved_payload["experiment_type"] == "multi_seed_policy_comparison"
    assert saved_payload["episodes_per_seed"] == 5
    assert saved_payload["seeds"] == [1, 7]
    assert set(saved_payload["aggregate_metrics"].keys()) == {
        "rules",
        "ai_review",
        "feedback_adjusted",
    }

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 6
    assert set(rows[0].keys()) == {
        "policy",
        "seed",
        "accuracy",
        "average_reward",
        "false_approve_rate",
        "false_reject_rate",
        "escalation_rate",
        "total_cases",
        "failure_count",
    }


def test_multi_seed_experiment_is_reproducible_for_same_seeds(
    tmp_path: Path,
) -> None:
    first = run_multi_seed_experiment(
        episodes=10,
        seeds=[1, 7],
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    second = run_multi_seed_experiment(
        episodes=10,
        seeds=[1, 7],
        dataset_path=DATASET_PATH,
        output_dir=tmp_path,
        write_files=False,
    )

    def comparable_runs(payload: dict) -> list[dict]:
        comparable = []

        for run in payload["runs"]:
            metrics = dict(run["metrics"])
            metrics.pop("runtime_seconds", None)

            comparable.append(
                {
                    "policy": run["policy"],
                    "seed": run["seed"],
                    "episodes": run["episodes"],
                    "metrics": metrics,
                    "feedback_policy_state": run["feedback_policy_state"],
                }
            )

        return comparable

    assert comparable_runs(first) == comparable_runs(second)
    assert first["aggregate_metrics"] == second["aggregate_metrics"]


def test_multi_seed_experiment_rejects_invalid_episode_count(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        run_multi_seed_experiment(
            episodes=0,
            seeds=[1, 7],
            dataset_path=DATASET_PATH,
            output_dir=tmp_path,
            write_files=False,
        )


def test_multi_seed_experiment_rejects_empty_seed_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_multi_seed_experiment(
            episodes=5,
            seeds=[],
            dataset_path=DATASET_PATH,
            output_dir=tmp_path,
            write_files=False,
        )