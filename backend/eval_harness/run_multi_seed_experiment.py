from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from eval_harness.environment import DEFAULT_DATASET_PATH
from eval_harness.metrics import DECISION_ORDER
from eval_harness.run_experiment import (
    DEFAULT_OUTPUT_DIR,
    PolicyName,
    run_experiment,
)


DEFAULT_SEEDS = [1, 7, 21, 42, 100]
DEFAULT_POLICIES: tuple[PolicyName, ...] = (
    "rules",
    "ai_review",
    "feedback_adjusted",
)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return statistics.mean(values)


def _std(values: list[float]) -> float:
    """
    Return population standard deviation for a fixed set of evaluated seeds.

    This keeps the report stable and easy to interpret for small synthetic
    experiment runs.
    """
    if len(values) <= 1:
        return 0.0

    return statistics.pstdev(values)


def _metric_values(
    runs: list[dict],
    *,
    policy_name: str,
    metric_name: str,
) -> list[float]:
    return [
        float(run["metrics"].get(metric_name, 0.0))
        for run in runs
        if run["policy"] == policy_name
    ]


def _sum_metric(
    runs: list[dict],
    *,
    policy_name: str,
    metric_name: str,
) -> int:
    return sum(
        int(run["metrics"].get(metric_name, 0))
        for run in runs
        if run["policy"] == policy_name
    )


def _aggregate_decision_distribution(
    runs: list[dict],
    *,
    policy_name: str,
) -> dict:
    matching_runs = [run for run in runs if run["policy"] == policy_name]

    distribution_total = {
        decision: sum(
            int(run["metrics"]["decision_distribution"].get(decision, 0))
            for run in matching_runs
        )
        for decision in DECISION_ORDER
    }

    distribution_rate_mean = {
        decision: _mean(
            [
                float(
                    run["metrics"]["decision_distribution_rate"].get(
                        decision,
                        0.0,
                    )
                )
                for run in matching_runs
            ]
        )
        for decision in DECISION_ORDER
    }

    return {
        "total": distribution_total,
        "mean_rate": distribution_rate_mean,
    }


def _aggregate_policy_metrics(
    runs: list[dict],
    *,
    policies: Iterable[PolicyName],
) -> dict:
    aggregate_metrics: dict[str, dict] = {}

    for policy_name in policies:
        policy_key = str(policy_name)

        accuracy_values = _metric_values(
            runs,
            policy_name=policy_key,
            metric_name="accuracy",
        )
        average_reward_values = _metric_values(
            runs,
            policy_name=policy_key,
            metric_name="average_reward",
        )
        false_approve_values = _metric_values(
            runs,
            policy_name=policy_key,
            metric_name="false_approve_rate",
        )
        false_reject_values = _metric_values(
            runs,
            policy_name=policy_key,
            metric_name="false_reject_rate",
        )
        escalation_values = _metric_values(
            runs,
            policy_name=policy_key,
            metric_name="escalation_rate",
        )

        aggregate_metrics[policy_key] = {
            "run_count": len(accuracy_values),
            "accuracy_mean": _mean(accuracy_values),
            "accuracy_std": _std(accuracy_values),
            "average_reward_mean": _mean(average_reward_values),
            "average_reward_std": _std(average_reward_values),
            "false_approve_rate_mean": _mean(false_approve_values),
            "false_approve_rate_std": _std(false_approve_values),
            "false_reject_rate_mean": _mean(false_reject_values),
            "false_reject_rate_std": _std(false_reject_values),
            "escalation_rate_mean": _mean(escalation_values),
            "escalation_rate_std": _std(escalation_values),
            "failure_count_total": _sum_metric(
                runs,
                policy_name=policy_key,
                metric_name="failure_count",
            ),
            "total_evaluated_cases": _sum_metric(
                runs,
                policy_name=policy_key,
                metric_name="total_cases",
            ),
            "decision_distribution_summary": _aggregate_decision_distribution(
                runs,
                policy_name=policy_key,
            ),
        }

    return aggregate_metrics


def _build_output_filename(*, generated_at: datetime) -> str:
    timestamp = generated_at.strftime("%Y-%m-%d-%H%M%S")
    return f"{timestamp}-multi-seed-policy-comparison"


def _write_json_result(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)


def _write_csv_records(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "policy",
        "seed",
        "accuracy",
        "average_reward",
        "false_approve_rate",
        "false_reject_rate",
        "escalation_rate",
        "total_cases",
        "failure_count",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            metrics = record["metrics"]

            writer.writerow(
                {
                    "policy": record["policy"],
                    "seed": record["seed"],
                    "accuracy": metrics["accuracy"],
                    "average_reward": metrics["average_reward"],
                    "false_approve_rate": metrics["false_approve_rate"],
                    "false_reject_rate": metrics["false_reject_rate"],
                    "escalation_rate": metrics["escalation_rate"],
                    "total_cases": metrics["total_cases"],
                    "failure_count": metrics["failure_count"],
                }
            )


def run_multi_seed_experiment(
    *,
    episodes: int = 50,
    seeds: list[int] | None = None,
    policies: tuple[PolicyName, ...] = DEFAULT_POLICIES,
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    write_files: bool = True,
) -> dict:
    """
    Run a reproducible multi-seed policy comparison experiment.

    This wraps the existing single-seed runner and aggregates metrics across
    several deterministic seeds. It is intentionally lightweight and uses
    synthetic cases only.
    """
    if episodes <= 0:
        raise ValueError("episodes must be greater than 0.")

    selected_seeds = DEFAULT_SEEDS if seeds is None else seeds

    if not selected_seeds:
        raise ValueError("At least one seed is required.")

    started_at = time.perf_counter()
    runs: list[dict] = []

    for policy_name in policies:
        for seed in selected_seeds:
            single_run = run_experiment(
                policy_name=policy_name,
                episodes=episodes,
                seed=seed,
                dataset_path=dataset_path,
                output_dir=output_dir,
                write_files=False,
            )

            runs.append(
                {
                    "policy": policy_name,
                    "seed": seed,
                    "episodes": episodes,
                    "metrics": single_run["metrics"],
                    "feedback_policy_state": single_run["feedback_policy_state"],
                }
            )

    aggregate_metrics = _aggregate_policy_metrics(
        runs,
        policies=policies,
    )

    runtime_seconds = time.perf_counter() - started_at
    generated_at = datetime.now(timezone.utc)
    output_dir_path = Path(output_dir)
    base_filename = _build_output_filename(generated_at=generated_at)

    json_output_path = output_dir_path / f"{base_filename}.json"
    csv_output_path = output_dir_path / f"{base_filename}.csv"

    payload = {
        "experiment_type": "multi_seed_policy_comparison",
        "generated_at": generated_at.isoformat(),
        "dataset": Path(dataset_path).name,
        "dataset_path": str(dataset_path),
        "episodes_per_seed": episodes,
        "seeds": selected_seeds,
        "policies": list(policies),
        "aggregate_metrics": aggregate_metrics,
        "runs": runs,
        "runtime_seconds": runtime_seconds,
        "output_files": {
            "json": str(json_output_path),
            "csv": str(csv_output_path),
        },
        "limitations": [
            "Synthetic dataset only.",
            "No real fraud labels are used.",
            "Feedback-adjusted policy uses simple threshold updates, not a trained reinforcement learning agent.",
            "AI-review fallback is deterministic for offline reproducible evaluation unless connected to saved or live AI outputs.",
            "Metrics measure synthetic decision behaviour only and should not be interpreted as production fraud-model performance.",
        ],
    }

    if write_files:
        _write_json_result(payload, json_output_path)
        _write_csv_records(runs, csv_output_path)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a multi-seed lightweight policy comparison experiment over "
            "synthetic verification cases."
        )
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=50,
        help="Number of synthetic policy episodes to run per seed.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=DEFAULT_SEEDS,
        help="Random seeds for reproducible case sampling.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to synthetic JSONL dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where JSON/CSV experiment outputs are written.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    payload = run_multi_seed_experiment(
        episodes=args.episodes,
        seeds=args.seeds,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        write_files=True,
    )

    print(json.dumps(payload["aggregate_metrics"], indent=2, sort_keys=True))
    print(f"Saved JSON: {payload['output_files']['json']}")
    print(f"Saved CSV: {payload['output_files']['csv']}")


if __name__ == "__main__":
    main()