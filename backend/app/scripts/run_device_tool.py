from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from app.db.session import SessionLocal
from app.crud.case import get_case
from app.services.tool_execution import run_device_risk_tool


async def main(case_id: str):
    db = SessionLocal()

    try:
        case = get_case(db, UUID(case_id))

        if not case:
            print("Case not found")
            return

        tool_run = await run_device_risk_tool(
            db,
            case=case,
        )

        print("Tool executed successfully")
        print("tool_run_id:", tool_run.id)
        print("score:", tool_run.score)
        print("confidence:", tool_run.confidence)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))