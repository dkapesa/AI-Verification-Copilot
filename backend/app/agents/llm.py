# backend/app/agents/llm.py
from __future__ import annotations

import json
from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.schemas import DecisionOutput
from app.core.config import settings


class DecisionModelProvider(ABC):
    @abstractmethod
    async def generate_decision(self, user_input: str) -> DecisionOutput:
        raise NotImplementedError


class OpenAIDecisionProvider(DecisionModelProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_decision(self, user_input: str) -> DecisionOutput:
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "decision_output",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "decision": {
                                "type": "string",
                                "enum": ["APPROVE", "ESCALATE", "REJECT"],
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                            },
                            "recommended_next_steps": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "decision",
                            "confidence",
                            "reasons",
                            "recommended_next_steps",
                        ],
                    },
                    "strict": True,
                }
            },
        )

        raw_text = response.output_text
        try:
            payload = json.loads(raw_text)
            return DecisionOutput.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid structured decision output: {exc}") from exc


def get_decision_provider() -> DecisionModelProvider:
    provider = settings.model_provider.lower()

    if provider == "openai":
        return OpenAIDecisionProvider()

    raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")