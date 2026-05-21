"""LangGraph 工作流定义（统一 Agent 版）。"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from lyra4d.state.graph_state import GraphState
from lyra4d.graph.unified_agent import node_init, node_agent, node_delivery, route_agent, tool_node


def build_workflow():
    """构建 LangGraph 工作流。

    流程：init → agent → route_agent
                        ├→ tools    → agent（工具调用循环）
                        ├→ delivery → END（最终交付）
                        └→ END（安全兜底）
    """
    workflow = StateGraph(GraphState)

    # 注册节点
    workflow.add_node("init", node_init)
    workflow.add_node("agent", node_agent)
    workflow.add_node("tools", tool_node)
    workflow.add_node("delivery", node_delivery)

    # 入口
    workflow.set_entry_point("init")

    # 固定边
    workflow.add_edge("init", "agent")
    workflow.add_edge("tools", "agent")
    workflow.add_edge("delivery", END)

    # 条件边：agent → (tools | delivery | end)
    workflow.add_conditional_edges(
        "agent",
        route_agent,
        {
            "tools": "tools",
            "delivery": "delivery",
            "end": END,
        },
    )

    return workflow.compile(checkpointer=MemorySaver())


_compiled_workflow = None


def get_workflow():
    """获取编译后的工作流（单例模式）。"""
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = build_workflow()
    return _compiled_workflow
