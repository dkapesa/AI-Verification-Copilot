from __future__ import annotations

import argparse
import csv
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from eval_harness.environment import (
    DEFAULT_DATASET_PATH,
    VerificationFeedbackEnvironment,
)
from eval_harness.metrics import summarize_results
from eval_harness.policies import (
    FeedbackAdjustedPolicy,
    ai_review_policy,
    rules_policy,
)
from eval_harness.schemas import DecisionAction, EvaluationStepResult, PolicyDecision


PolicyName = Literal["rules", "ai_review", "feedback_adjusted"]


DEFAULT_OUTPUT_DIR = Path("experiments") / "runs"


def _select_policy_decision(
    *,
    policy_name: PolicyName,
    environment: VerificationFeedbackEnvironment,
    case_id: str,
    feedback_policy: FeedbackAdjustedPolicy | None,
) -> PolicyDecision:
    case = environment.get_case(case_id)

    if policy_name == "rules":
        return rules_policy(case)

    if policy_name == "ai_review":
        return ai_review_policy(case)

    if policy_name == "feedback_adjusted":
        if feedback_policy is None:
            raise ValueError("feedback_policy is required for feedback_adjusted runs.")
        return feedback_policy.decide(case)

    raise ValueError(f"Unsupported policy name: {policy_name}")


def _write_json_result(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)


def _write_csv_records(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "episode",
        "case_id",
        "decision",
        "expected_decision",
        "reward",
        "correct",
        "reward_reason",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            writer.writerow(
                {
                    "episode": record["episode"],
                    "case_id": record["case_id"],
                    "decision": record["decision"],
                    "expected_decision": record["expected_decision"],
                    "reward": record["reward"],
                    "correct": record["correct"],
                    "reward_reason": record["metadata"].get("reward_reason"),
                }
            )


def _build_run_filename(
    *,
    generated_at: datetime,
    policy_name: str,
    seed: int,
) -> str:
    timestamp = generated_at.strftime("%Y-%m-%d-%H%M%S")
    return f"{timestamp}-{policy_name}-policy-seed-{seed}"


def run_experiment(
    *,
    policy_name: PolicyName,
    episodes: int,
    seed: int,
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    write_files: bool = True,
) -> dict:
    """
    Run a reproducible lightweight policy evaluation experiment.

    This is intentionally small and deterministic. It treats synthetic cases as
    states, decisions as actions, and downstream outcomes as reward feedback.
    """
    if episodes <= 0:
        raise ValueError("episodes must be greater than 0.")

    environment = VerificationFeedbackEnvironment.from_jsonl(dataset_path)
    rng = random.Random(seed)
    feedback_policy = (
        FeedbackAdjustedPolicy()
        if policy_name == "feedback_adjusted"
        else None
    )

    started_at = time.perf_counter()
    results: list[EvaluationStepResult] = []
    decision_records: list[dict] = []
    failure_count = 0

    case_ids = [case.case_id for case in environment.cases]

    for episode in range(1, episodes + 1):
        case_id = rng.choice(case_ids)

        try:
            policy_decision = _select_policy_decision(
                policy_name=policy_name,
                environment=environment,
                case_id=case_id,
                feedback_policy=feedback_policy,
            )

            step_result = environment.step(case_id, policy_decision.decision)
            results.append(step_result)

            if feedback_policy is not None:
                feedback_policy.update(
                    case=environment.get_case(case_id),
                    decision=policy_decision.decision,
                    reward=step_result.reward,
                )

            decision_records.append(
                {
                    "episode": episode,
                    "case_id": step_result.case_id,
                    "decision": step_result.decision,
                    "expected_decision": step_result.expected_decision,
                    "reward": step_result.reward,
                    "correct": step_result.correct,
                    "metadata": step_result.metadata,
                    "policy_confidence": policy_decision.confidence,
                    "policy_rationale": policy_decision.rationale,
                }
            )

        except Exception as exc:
            failure_count += 1
            decision_records.append(
                {
                    "episode": episode,
                    "case_id": case_id,
                    "decision": None,
                    "expected_decision": None,
                    "reward": None,
                    "correct": False,
                    "metadata": {
                        "error": str(exc),
                    },
                    "policy_confidence": None,
                    "policy_rationale": None,
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
    base_filename = _build_run_filename(
        generated_at=generated_at,
        policy_name=policy_name,
        seed=seed,
    )

    json_output_path = output_dir_path / f"{base_filename}.json"
    csv_output_path = output_dir_path / f"{base_filename}.csv"

    payload = {
        "experiment_name": "learning_from_feedback_evaluation_harness",
        "generated_at": generated_at.isoformat(),
        "policy_name": policy_name,
        "episodes": episodes,
        "seed": seed,
        "dataset_path": str(dataset_path),
        "metrics": metrics,
        "feedback_policy_state": (
            {
                "approve_threshold": feedback_policy.approve_threshold,
                "reject_threshold": feedback_policy.reject_threshold,
                "learning_rate": feedback_policy.learning_rate,
                "history_length": len(feedback_policy.history),
            }
            if feedback_policy is not None
            else None
        ),
        "decision_records": decision_records,
        "output_files": {
            "json": str(json_output_path),
            "csv": str(csv_output_path),
        },
    }

    if write_files:
        _write_json_result(payload, json_output_path)
        _write_csv_records(decision_records, csv_output_path)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a lightweight learning-from-feedback evaluation experiment "
            "over synthetic verification cases."
        )
    )

    parser.add_argument(
        "--policy",
        choices=["rules", "ai_review", "feedback_adjusted"],
        required=True,
        help="Policy to evaluate.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=100,
        help="Number of synthetic policy episodes to run.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible case sampling.",
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

    payload = run_experiment(
        policy_name=args.policy,
        episodes=args.episodes,
        seed=args.seed,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        write_files=True,
    )

    print(json.dumps(payload["metrics"], indent=2, sort_keys=True))
    print(f"Saved JSON: {payload['output_files']['json']}")
    print(f"Saved CSV: {payload['output_files']['csv']}")


if __name__ == "__main__":
    main()