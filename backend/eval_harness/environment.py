from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from eval_harness.schemas import (
    EvaluationStepResult,
    SyntheticCase,
    VALID_DECISIONS,
)


DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "synthetic_cases.jsonl"
)


def load_synthetic_cases(path: Path | str = DEFAULT_DATASET_PATH) -> list[SyntheticCase]:
    """
    Load synthetic evaluation cases from JSONL.

    The dataset is intentionally synthetic. It is used for deterministic
    policy evaluation and feedback-loop experiments, not as production fraud data.
    """
    dataset_path = Path(path)

    cases: list[SyntheticCase] = []

    with dataset_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                payload = json.loads(stripped)
                cases.append(SyntheticCase.model_validate(payload))
            except Exception as exc:
                raise ValueError(
                    f"Invalid synthetic case at line {line_number} in {dataset_path}"
                ) from exc

    return cases


def _validate_action(action: str) -> None:
    if action not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision action: {action}. "
            f"Expected one of {sorted(VALID_DECISIONS)}."
        )


def calculate_reward(case: SyntheticCase, action: str) -> tuple[float, dict]:
    """
    Deterministic reward function for synthetic fraud-review evaluation.

    This intentionally models asymmetric costs:
    - false approval of a fraud case is most costly
    - false rejection of a good case is also costly
    - escalation is safer but carries operational cost
    - appropriate escalation gets partial credit because it preserves review quality
      while avoiding overclaiming certainty
    """
    _validate_action(action)

    expected = case.expected_decision
    metadata = {
        "expected_decision": expected,
        "action": action,
        "fraud_confirmed": case.outcome.fraud_confirmed,
        "manual_review_needed": case.outcome.manual_review_needed,
        "customer_harm_risk": case.outcome.customer_harm_risk,
        "reward_reason": None,
    }

    if action == expected:
        if action == "ESCALATE":
            metadata["reward_reason"] = "appropriate_escalation"
            return 0.5, metadata

        metadata["reward_reason"] = "correct_decision"
        return 1.0, metadata

    if action == "APPROVE" and expected == "REJECT":
        metadata["reward_reason"] = "false_approve_confirmed_fraud"
        return -2.0, metadata

    if action == "REJECT" and expected == "APPROVE":
        metadata["reward_reason"] = "false_reject_legitimate_case"
        return -1.0, metadata

    if action == "ESCALATE" and expected in {"APPROVE", "REJECT"}:
        metadata["reward_reason"] = "unnecessary_escalation"
        return -0.3, metadata

    if action == "APPROVE" and expected == "ESCALATE":
        metadata["reward_reason"] = "approved_case_needing_manual_review"
        return -0.8, metadata

    if action == "REJECT" and expected == "ESCALATE":
        metadata["reward_reason"] = "rejected_uncertain_case"
        return -0.5, metadata

    metadata["reward_reason"] = "unclassified_mismatch"
    return -0.5, metadata


class VerificationFeedbackEnvironment:
    """
    Lightweight deterministic environment for offline policy evaluation.

    Conceptual mapping:
    - state: synthetic case signals
    - action: APPROVE / ESCALATE / REJECT
    - reward: deterministic feedback score based on expected decision and outcome
    """

    def __init__(self, cases: Iterable[SyntheticCase]) -> None:
        self.cases = list(cases)

        if not self.cases:
            raise ValueError("VerificationFeedbackEnvironment requires at least one case.")

        self._cases_by_id = {case.case_id: case for case in self.cases}

        if len(self._cases_by_id) != len(self.cases):
            raise ValueError("Synthetic cases must have unique case_id values.")

    @classmethod
    def from_jsonl(
        cls,
        path: Path | str = DEFAULT_DATASET_PATH,
    ) -> "VerificationFeedbackEnvironment":
        return cls(load_synthetic_cases(path))

    def get_case(self, case_id: str) -> SyntheticCase:
        try:
            return self._cases_by_id[case_id]
        except KeyError as exc:
            raise KeyError(f"Unknown synthetic case_id: {case_id}") from exc

    def get_state(self, case_id: str) -> dict:
        case = self.get_case(case_id)
        return case.signals.model_dump()

    def step(self, case_id: str, action: str) -> EvaluationStepResult:
        case = self.get_case(case_id)
        reward, metadata = calculate_reward(case, action)

        return EvaluationStepResult(
            case_id=case.case_id,
            decision=action,  # type: ignore[arg-type]
            expected_decision=case.expected_decision,
            reward=reward,
            correct=action == case.expected_decision,
            outcome=case.outcome,
            metadata=metadata,
        )