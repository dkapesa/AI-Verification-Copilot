from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval_harness.environment import DEFAULT_DATASET_PATH
from eval_harness.run_experiment import DEFAULT_OUTPUT_DIR
from eval_harness.saved_ai_review_evaluator import (
    DEFAULT_SAVED_AI_REVIEW_INPUT_PATH,
    evaluate_saved_ai_reviews,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate saved structured AI review outputs against synthetic "
            "verification expected outcomes without live model calls."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_SAVED_AI_REVIEW_INPUT_PATH,
        help="Path to saved AI review JSONL fixture.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to synthetic verification JSONL dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where JSON/CSV evaluation outputs are written.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    payload = evaluate_saved_ai_reviews(
        input_path=args.input,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        write_files=True,
    )

    print(json.dumps(payload["metrics"], indent=2, sort_keys=True))
    print(f"Saved JSON: {payload['output_files']['json']}")
    print(f"Saved CSV: {payload['output_files']['csv']}")


if __name__ == "__main__":
    main()
