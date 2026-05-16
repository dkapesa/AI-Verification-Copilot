from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DecisionAction = Literal["APPROVE", "ESCALATE", "REJECT"]
CustomerHarmRisk = Literal["low", "medium", "high"]


VALID_DECISIONS: set[str] = {"APPROVE", "ESCALATE", "REJECT"}


class CaseSignals(BaseModel):
    """
    Structured synthetic state used by the evaluation harness.

    Values are normalized to [0.0, 1.0] so policies can be compared
    with deterministic threshold logic.
    """

    device_risk: float = Field(ge=0.0, le=1.0)
    behaviour_anomaly: float = Field(ge=0.0, le=1.0)
    document_confidence: float = Field(ge=0.0, le=1.0)
    watchlist_match: bool
    velocity_score: float = Field(ge=0.0, le=1.0)


class CaseOutcome(BaseModel):
    """
    Synthetic downstream outcome used as feedback.

    This is not production fraud-label data. It is a controlled toy signal
    for testing policy behavior and reward assumptions.
    """

    fraud_confirmed: bool
    manual_review_needed: bool
    customer_harm_risk: CustomerHarmRisk


class SyntheticCase(BaseModel):
    """
    One synthetic verification case for offline evaluation.
    """

    case_id: str = Field(min_length=1)
    signals: CaseSignals
    expected_decision: DecisionAction
    outcome: CaseOutcome


class PolicyDecision(BaseModel):
    """
    Policy output for a single synthetic case.
    """

    case_id: str
    decision: DecisionAction
    policy_name: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = None


class EvaluationStepResult(BaseModel):
    """
    Result of applying one decision action to one synthetic case.
    """

    case_id: str
    decision: DecisionAction
    expected_decision: DecisionAction
    reward: float
    correct: bool
    outcome: CaseOutcome
    metadata: dict = Field(default_factory=dict)