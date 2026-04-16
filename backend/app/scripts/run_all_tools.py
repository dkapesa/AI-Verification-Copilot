from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from app.crud.case import get_case
from app.db.session import SessionLocal
from app.services.tool_runner import run_tools_parallel
from app.tools.schemas import ToolCaseInput


async def main(case_id: str) -> None:
    db = SessionLocal()

    try:
        case = get_case(db, UUID(case_id))
        if not case:
            print("Case not found")
            return

        case_input = ToolCaseInput(
            case_id=case.id,
            user_id=case.user_id,
            email=case.email,
            device_info=case.device_info or {},
            document_check_result=case.document_check_result or {},
            behaviour_summary=case.behaviour_summary or {},
        )

        results = await run_tools_parallel(case_input)

        print(f"Ran {len(results)} tools")
        for result in results:
            print(
                f"{result.tool_name}: "
                f"status={result.status}, "
                f"score={result.score}, "
                f"confidence={result.confidence}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))