# backend/app/agents/graph.py
from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes.aggregate import aggregate_node
from app.agents.nodes.decide import decision_node
from app.agents.nodes.execute_tools import build_execute_tools_node
from app.agents.nodes.intake import build_intake_node
from app.agents.nodes.persist import build_persist_node
from app.agents.nodes.planner import planner_node
from app.agents.state import AgentState


def build_review_graph(db: Session):
    graph = StateGraph(AgentState)

    graph.add_node("intake", build_intake_node(db))
    graph.add_node("planner", planner_node)
    graph.add_node("execute_tools", build_execute_tools_node())
    graph.add_node("aggregate", aggregate_node)
    graph.add_node("decide", decision_node)
    graph.add_node("persist", build_persist_node(db))

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "planner")
    graph.add_edge("planner", "execute_tools")
    graph.add_edge("execute_tools", "aggregate")
    graph.add_edge("aggregate", "decide")
    graph.add_edge("decide", "persist")
    graph.add_edge("persist", END)

    return graph.compile()