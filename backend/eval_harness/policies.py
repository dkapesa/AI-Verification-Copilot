from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, cast

from eval_harness.schemas import DecisionAction, PolicyDecision, SyntheticCase, VALID_DECISIONS


def calculate_risk_score(case: SyntheticCase) -> float:
    """
    Convert synthetic verification signals into a simple risk score.

    This is intentionally deterministic and lightweight. It is not a trained
    risk model; it provides a stable baseline for policy comparison.
    """
    signals = case.signals

    document_risk = 1.0 - signals.document_confidence
    watchlist_risk = 1.0 if signals.watchlist_match else 0.0

    risk_score = max(
        signals.device_risk,
        signals.behaviour_anomaly,
        signals.velocity_score,
        document_risk,
        watchlist_risk,
    )

    return min(max(risk_score, 0.0), 1.0)


def _confidence_from_risk(risk_score: float) -> float:
    """
    Produce a bounded confidence proxy from distance away from uncertainty.

    Scores close to 0.5 are less confident. Scores closer to 0 or 1 are more
    confident. This is a deterministic proxy, not calibrated probability.
    """
    confidence = 0.55 + abs(risk_score - 0.5)
    return min(max(confidence, 0.0), 0.95)


def _build_policy_decision(
    *,
    case: SyntheticCase,
    decision: str,
    policy_name: str,
    confidence: float | None,
    rationale: str,
) -> PolicyDecision:
    if decision not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid policy decision: {decision}. "
            f"Expected one of {sorted(VALID_DECISIONS)}."
        )

    return PolicyDecision(
        case_id=case.case_id,
        decision=cast(DecisionAction, decision),
        policy_name=policy_name,
        confidence=confidence,
        rationale=rationale,
    )


def rules_policy(case: SyntheticCase) -> PolicyDecision:
    """
    Deterministic baseline policy using hand-authored thresholds.

    This represents a simple rules policy an operations team might use before
    introducing model-assisted review or feedback adjustment.
    """
    risk_score = calculate_risk_score(case)

    if case.signals.watchlist_match or case.signals.document_confidence < 0.30:
        decision = "REJECT"
        rationale = "Rejected due to watchlist match or very low document confidence."
    elif risk_score >= 0.78:
        decision = "REJECT"
        rationale = "Rejected due to high aggregate risk score."
    elif risk_score >= 0.45 or case.signals.document_confidence < 0.65:
        decision = "ESCALATE"
        rationale = "Escalated due to moderate risk or uncertain document confidence."
    else:
        decision = "APPROVE"
        rationale = "Approved due to low aggregate risk and sufficient document confidence."

    return _build_policy_decision(
        case=case,
        decision=decision,
        policy_name="rules_policy",
        confidence=_confidence_from_risk(risk_score),
        rationale=rationale,
    )


def ai_review_policy(
    case: SyntheticCase,
    mocked_decisions_by_case_id: Mapping[str, DecisionAction] | None = None,
) -> PolicyDecision:
    """
    Lightweight AI-review policy for offline evaluation.

    In this harness, the AI policy can consume mocked decisions so automated
    experiments do not require live OpenAI calls. If no mocked decision is
    provided, it falls back to a conservative deterministic approximation.
    """
    risk_score = calculate_risk_score(case)

    if mocked_decisions_by_case_id and case.case_id in mocked_decisions_by_case_id:
        decision = mocked_decisions_by_case_id[case.case_id]
        rationale = "Used mocked AI review decision for reproducible offline evaluation."
    elif case.signals.watchlist_match:
        decision = "REJECT"
        rationale = "Rejected because watchlist match is treated as high-confidence risk."
    elif risk_score >= 0.75 and case.signals.document_confidence < 0.45:
        decision = "REJECT"
        rationale = "Rejected due to high risk score and weak document confidence."
    elif risk_score >= 0.40:
        decision = "ESCALATE"
        rationale = "Escalated because risk score is within the uncertain review band."
    else:
        decision = "APPROVE"
        rationale = "Approved because risk score is below AI review escalation threshold."

    return _build_policy_decision(
        case=case,
        decision=decision,
        policy_name="ai_review_policy",
        confidence=_confidence_from_risk(risk_score),
        rationale=rationale,
    )


@dataclass
class FeedbackAdjustedPolicy:
    """
    Simple feedback-adjusted threshold policy.

    This is not a full reinforcement learning algorithm. It is a lightweight
    policy-improvement loop that adjusts thresholds after receiving reward
    feedback from synthetic outcomes.
    """

    approve_threshold: float = 0.45
    reject_threshold: float = 0.78
    learning_rate: float = 0.05
    min_threshold_gap: float = 0.10
    history: list[dict] = field(default_factory=list)

    policy_name: str = "feedback_adjusted_policy"

    def __post_init__(self) -> None:
        if self.approve_threshold >= self.reject_threshold:
            raise ValueError("approve_threshold must be lower than reject_threshold.")

        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")

    def decide(self, case: SyntheticCase) -> PolicyDecision:
        risk_score = calculate_risk_score(case)

        if risk_score >= self.reject_threshold:
            decision = "REJECT"
            rationale = (
                "Rejected because risk score exceeded the feedback-adjusted "
                "reject threshold."
            )
        elif risk_score >= self.approve_threshold:
            decision = "ESCALATE"
            rationale = (
                "Escalated because risk score fell between feedback-adjusted "
                "approval and rejection thresholds."
            )
        else:
            decision = "APPROVE"
            rationale = (
                "Approved because risk score remained below the feedback-adjusted "
                "approval threshold."
            )

        return _build_policy_decision(
            case=case,
            decision=decision,
            policy_name=self.policy_name,
            confidence=_confidence_from_risk(risk_score),
            rationale=rationale,
        )

    def update(
        self,
        *,
        case: SyntheticCase,
        decision: DecisionAction,
        reward: float,
    ) -> None:
        """
        Update thresholds after observing reward.

        The update rules are deliberately simple and inspectable:
        - false approve: become more cautious by lowering approve threshold
        - false reject: become less aggressive by raising reject threshold
        - unnecessary escalation of clear approval: approve more readily
        - escalation when rejection was expected: reject more readily
        """
        old_approve_threshold = self.approve_threshold
        old_reject_threshold = self.reject_threshold

        expected = case.expected_decision

        if reward < 0:
            if decision == "APPROVE" and expected in {"ESCALATE", "REJECT"}:
                self.approve_threshold -= self.learning_rate

            elif decision == "REJECT" and expected in {"APPROVE", "ESCALATE"}:
                self.reject_threshold += self.learning_rate

            elif decision == "ESCALATE" and expected == "APPROVE":
                self.approve_threshold += self.learning_rate

            elif decision == "ESCALATE" and expected == "REJECT":
                self.reject_threshold -= self.learning_rate

        self._clip_thresholds()

        self.history.append(
            {
                "case_id": case.case_id,
                "decision": decision,
                "expected_decision": expected,
                "reward": reward,
                "old_approve_threshold": old_approve_threshold,
                "old_reject_threshold": old_reject_threshold,
                "new_approve_threshold": self.approve_threshold,
                "new_reject_threshold": self.reject_threshold,
            }
        )

    def _clip_thresholds(self) -> None:
        self.approve_threshold = min(max(self.approve_threshold, 0.05), 0.90)
        self.reject_threshold = min(max(self.reject_threshold, 0.10), 0.95)

        if self.approve_threshold > self.reject_threshold - self.min_threshold_gap:
            midpoint = (self.approve_threshold + self.reject_threshold) / 2
            self.approve_threshold = max(0.05, midpoint - self.min_threshold_gap / 2)
            self.reject_threshold = min(0.95, midpoint + self.min_threshold_gap / 2)