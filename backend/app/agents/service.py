from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.graph import build_review_graph
from app.agents.schemas import AIReviewResponse
from app.agents.state import AgentState


async def run_ai_review(*, db: Session, case_id: UUID) -> AIReviewResponse:
    graph = build_review_graph(db)
    result = await graph.ainvoke(AgentState(case_id=case_id).model_dump())

    final_state = AgentState.model_validate(result)

    return AIReviewResponse(
        case_id=str(case_id),
        status="FAILED" if final_state.errors else "COMPLETED",
        decision=final_state.decision,
        aggregated_signals=final_state.aggregated_signals,
        tool_results_count=len(final_state.tool_outputs),
        errors=final_state.errors,
    )