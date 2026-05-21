"""LangGraph 状态定义。"""

from typing import TypedDict, Optional, Callable, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class GraphState(TypedDict, total=False):
    """LangGraph 工作流的全局状态。"""

    # --- 用户输入 ---
    user_input: str
    mode: str
    target_ai: str

    # --- 对话消息（核心） ---
    messages: Annotated[list[BaseMessage], add_messages]

    # --- 迭代控制 ---
    current_iteration: int
    max_iterations: int
    score_threshold: int
    current_score: int

    # --- 用户反馈 ---
    user_feedback: Optional[str]

    # --- 最终输出 ---
    final_prompt: str
    optimization_summary: str
    usage_tips: str
    final_score: int
    total_iterations: int
    d4_result: Optional[dict]

    # --- 内部 ---
    sse_callback: Optional[Callable]
