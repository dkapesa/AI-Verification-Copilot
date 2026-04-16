from __future__ import annotations

import asyncio
from typing import Iterable

from app.tools.registry import tool_registry
from app.tools.schemas import ToolCaseInput, ToolResult


async def run_tools_parallel(
    case_input: ToolCaseInput,
    tool_names: Iterable[str] | None = None,
) -> list[ToolResult]:
    """
    Execute multiple fraud tools concurrently.

    If tool_names is None, all registered tools will run.
    """

    if tool_names is None:
        tool_names = tool_registry.list_names()

    tool_calls = []

    for name in tool_names:
        tool_fn = tool_registry.get(name)
        tool_calls.append(tool_fn(case_input))

    results = await asyncio.gather(*tool_calls, return_exceptions=True)

    tool_results: list[ToolResult] = []

    for result in results:
        if isinstance(result, Exception):
            continue

        tool_results.append(result)

    return tool_results