# backend/app/agents/nodes/execute_tools.py
from __future__ import annotations

from app.agents.state import AgentState
from app.services.tool_runner import run_tools_parallel
from app.tools.schemas import ToolCaseInput


def build_execute_tools_node():
    async def execute_tools_node(state_dict: dict) -> dict:
        state = AgentState.model_validate(state_dict)

        if state.errors:
            return {}

        case_data = state.case_data or {}

        tool_input = ToolCaseInput(
            case_id=state.case_id,
            user_id=case_data.get("user_id"),
            email=case_data.get("email"),
            device_info=case_data.get("device_info") or {},
            document_check_result=case_data.get("document_check_result") or {},
            behaviour_summary=case_data.get("behaviour_summary") or {},
        )

        results = await run_tools_parallel(
            case_input=tool_input,
            tool_names=state.requested_tools,
        )

        normalized_results = [result.model_dump() for result in results]

        return {"tool_outputs": normalized_results}

    return execute_tools_node