# backend/app/agents/nodes/intake.py
from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.crud.case import get_case


def build_intake_node(db: Session):
    def intake_node(state_dict: dict) -> dict:
        state = AgentState.model_validate(state_dict)

        if state.started_at_ms is None:
            state.started_at_ms = int(time.time() * 1000)

        case = get_case(db, state.case_id)
        if not case:
            return {
                "errors": [f"Case not found: {state.case_id}"],
                "completed_at_ms": int(time.time() * 1000),
            }

        case_data = {
            "id": str(case.id),
            "user_id": case.user_id,
            "email": case.email,
            "status": case.status,
            "device_info": case.device_info or {},
            "document_check_result": case.document_check_result or {},
            "behaviour_summary": case.behaviour_summary or {},
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        }

        return {"case_data": case_data}
    return intake_node