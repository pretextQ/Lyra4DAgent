"""统一 Agent 节点定义。"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode
from lyra4d.graph.unified_prompt import UNIFIED_SYSTEM_PROMPT
from lyra4d.config.settings import get_settings
from lyra4d.utils.llm_helper import create_llm
from lyra4d.utils.agent_tools import evaluate_prompt, get_platform_tips, search_knowledge, search_history
from lyra4d.schemas.models import D4Output
from lyra4d.state.graph_state import GraphState
from lyra4d.utils.logger import logger

# 工具列表
TOOLS = [evaluate_prompt, get_platform_tips, search_knowledge, search_history]

# ToolNode
tool_node = ToolNode(TOOLS)


def _build_system_message(state: GraphState) -> SystemMessage:
    """用当前状态动态构建系统消息。"""
    prompt_text = UNIFIED_SYSTEM_PROMPT.format(
        current_iteration=state.get("current_iteration", 0),
        max_iterations=state.get("max_iterations", 3),
        score_threshold=state.get("score_threshold", 8),
        target_ai=state.get("target_ai", "general"),
        mode=state.get("mode", "detail"),
    )
    return SystemMessage(content=prompt_text)


def _extract_json(content: str, marker: str) -> dict | None:
    """从标记后的文本中提取 JSON。"""
    try:
        idx = content.index(marker)
        json_str = content[idx + len(marker):].strip()
        # 处理 markdown 代码块
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"[UnifiedAgent] JSON 解析失败: {e}")
        return None


# ---- 节点函数 ----


async def node_init(state: GraphState) -> dict:
    """初始化节点：构建初始消息。"""
    settings = get_settings()
    system_msg = SystemMessage(content=UNIFIED_SYSTEM_PROMPT.format(
        current_iteration=0,
        max_iterations=settings.max_iterations,
        score_threshold=settings.score_threshold,
        target_ai=state.get("target_ai", "general"),
        mode=state.get("mode", "detail"),
    ))
    human_msg = HumanMessage(content=f"请优化以下提示词：\n\n{state['user_input']}")

    print(f"[Init] 开始优化 | 需求: {state['user_input'][:50]}... | 平台: {state['target_ai']} | 模式: {state['mode']}")

    return {
        "messages": [system_msg, human_msg],
        "current_iteration": 0,
        "current_score": 0,
        "max_iterations": settings.max_iterations,
        "score_threshold": settings.score_threshold,
    }


async def node_agent(state: GraphState) -> dict:
    """核心 Agent 节点：调用 LLM，处理标记和中断。"""
    llm = create_llm(temperature=0.4)
    llm_with_tools = llm.bind_tools(TOOLS)

    # 重建系统消息（动态更新 iteration/score）
    messages = list(state["messages"])
    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = _build_system_message(state)
    else:
        messages.insert(0, _build_system_message(state))

    # 调用 LLM
    current_iter = state.get("current_iteration", 0)
    logger.info(f"[UnifiedAgent] 调用 LLM | 迭代: {current_iter} | 消息数: {len(messages)}")

    try:
        response = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        logger.error(f"[UnifiedAgent] LLM 调用异常: {type(e).__name__}: {e}")
        raise

    content = response.content if response.content else ""

    # 检测工具调用 → 交给 route_agent 路由到 ToolNode
    if response.tool_calls:
        logger.info(f"[UnifiedAgent] 工具调用: {[tc['name'] for tc in response.tool_calls]}")
        return {"messages": [response]}

    # 检测用户反馈标记
    if "###USER_FEEDBACK_REQUIRED###" in content:
        data = _extract_json(content, "###USER_FEEDBACK_REQUIRED###")
        draft = data.get("draft", content) if data else content
        score = data.get("score", 0) if data else 0
        improvement_points = data.get("improvement_points", []) if data else []

        current_iter += 1
        print(f"[UnifiedAgent] 第{current_iter}轮草稿完成 | 评分: {score}/10")

        # 中断：等待用户反馈
        feedback = interrupt({
            "draft": draft,
            "score": score,
            "improvement_points": improvement_points,
            "message": f"这是第{current_iter}轮优化结果，请审阅。输入修改意见继续优化，或输入'通过'直接进入交付。",
        })

        # 恢复：收到用户反馈
        print(f"[UnifiedAgent] 收到用户反馈: {str(feedback)[:50]}...")

        # 追加标记响应 + 用户反馈
        messages_to_add = [response, HumanMessage(content=str(feedback))]

        # 再次调用 LLM
        new_messages = list(state["messages"]) + messages_to_add
        if new_messages and isinstance(new_messages[0], SystemMessage):
            new_messages[0] = _build_system_message({
                **state,
                "current_iteration": current_iter,
                "current_score": score,
            })

        logger.info(f"[UnifiedAgent] 反馈后调用 LLM | 消息数: {len(new_messages)} | 反馈: {str(feedback)[:30]}")
        try:
            new_response = await llm_with_tools.ainvoke(new_messages)
        except Exception as e:
            logger.error(f"[UnifiedAgent] 反馈后 LLM 调用异常: {type(e).__name__}: {e}")
            raise
        new_content = new_response.content if new_response.content else ""

        # 检查新响应
        if new_response.tool_calls:
            logger.info(f"[UnifiedAgent] 反馈后工具调用: {[tc['name'] for tc in new_response.tool_calls]}")
            return {"messages": messages_to_add + [new_response], "current_iteration": current_iter, "current_score": score}

        if "###FINAL_DELIVERY###" in new_content:
            print(f"[UnifiedAgent] 准备交付")
            return {"messages": messages_to_add + [new_response], "current_iteration": current_iter, "current_score": score}

        if "###USER_FEEDBACK_REQUIRED###" in new_content:
            new_data = _extract_json(new_content, "###USER_FEEDBACK_REQUIRED###")
            new_score = new_data.get("score", score) if new_data else score
            current_iter += 1
            print(f"[UnifiedAgent] 第{current_iter}轮草稿完成 | 评分: {new_score}/10")
            return {"messages": messages_to_add + [new_response], "current_iteration": current_iter, "current_score": new_score}

        # 兜底
        return {"messages": messages_to_add + [new_response], "current_iteration": current_iter, "current_score": score}

    # 检测最终交付标记
    if "###FINAL_DELIVERY###" in content:
        print(f"[UnifiedAgent] 准备交付")
        return {"messages": [response]}

    # 无标记无工具调用 → 安全兜底
    logger.warning(f"[UnifiedAgent] LLM 输出无标记无工具调用，返回原响应")
    return {"messages": [response]}


async def node_delivery(state: GraphState) -> dict:
    """交付节点：解析最终输出。"""
    # 找到最后一条包含 ###FINAL_DELIVERY### 的消息
    content = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and "###FINAL_DELIVERY###" in (msg.content or ""):
            content = msg.content
            break

    data = _extract_json(content, "###FINAL_DELIVERY###")

    if data:
        try:
            d4_output = D4Output(**data)
        except Exception as e:
            logger.warning(f"[UnifiedAgent] D4Output 校验失败: {e}")
            d4_output = D4Output(
                final_prompt=data.get("final_prompt", content),
                optimization_summary=data.get("optimization_summary", ""),
                usage_tips=data.get("usage_tips", ""),
            )
    else:
        # JSON 解析失败的兜底
        fallback = content.split("###FINAL_DELIVERY###")[-1].strip() if "###FINAL_DELIVERY###" in content else content
        d4_output = D4Output(
            final_prompt=fallback,
            optimization_summary="",
            usage_tips="",
        )

    current_score = state.get("current_score", 0)
    current_iteration = state.get("current_iteration", 0)

    print(f"[UnifiedAgent] 交付完成！共迭代 {current_iteration} 轮，评分: {current_score}/10")
    print(f"[UnifiedAgent] 最终提示词: {d4_output.final_prompt[:100]}...")

    return {
        "final_prompt": d4_output.final_prompt,
        "optimization_summary": d4_output.optimization_summary,
        "usage_tips": d4_output.usage_tips,
        "d4_result": d4_output.model_dump(),
        "final_score": current_score,
        "total_iterations": current_iteration,
    }


def route_agent(state: GraphState) -> str:
    """条件路由：根据最后一条消息决定下一步。"""
    if not state.get("messages"):
        return "end"

    last_msg = state["messages"][-1]

    # 只检查 AIMessage
    if not isinstance(last_msg, AIMessage):
        return "end"

    # 工具调用
    if last_msg.tool_calls:
        return "tools"

    content = last_msg.content or ""

    # 最终交付
    if "###FINAL_DELIVERY###" in content:
        return "delivery"

    # 兜底
    return "end"
