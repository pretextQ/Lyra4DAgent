"""Agent 工具定义。"""

from langchain_core.tools import tool
from typing import Annotated


@tool
def evaluate_prompt(
    prompt: Annotated[str, "要评估的提示词内容"],
    criteria: Annotated[list[str], "评估标准列表，如：['清晰度', '完整性', '结构化']"],
) -> str:
    """评估提示词质量，返回评分和具体改进点。当需要判断当前提示词草稿的质量时调用此工具。"""
    score = 5
    issues = []

    # 长度检查
    if len(prompt) < 50:
        issues.append("提示词过短，缺少足够的上下文和约束")
        score -= 1
    elif len(prompt) > 2000:
        issues.append("提示词过长，可能导致模型注意力分散")
        score -= 1
    else:
        score += 1

    # 结构检查
    if "角色" in prompt or "你是" in prompt or "role" in prompt.lower():
        score += 1
    else:
        issues.append("缺少角色设定，建议添加'你是...'开头的角色描述")

    if "输出格式" in prompt or "格式要求" in prompt or "format" in prompt.lower():
        score += 1
    else:
        issues.append("缺少输出格式要求，模型可能返回不规范的结果")

    if "约束" in prompt or "注意" in prompt or "不要" in prompt:
        score += 1
    else:
        issues.append("缺少约束条件，建议添加限制和注意事项")

    if "示例" in prompt or "比如" in prompt or "例如" in prompt:
        score += 1
    else:
        issues.append("缺少示例，添加 1-2 个示例能显著提升输出质量")

    # 任务分解检查
    if "步骤" in prompt or "第一" in prompt or "1." in prompt:
        score += 1
    else:
        issues.append("建议将复杂任务分解为步骤")

    # 限制分数范围
    score = max(1, min(10, score))

    # 按 criteria 逐项评估
    criteria_results = []
    for c in criteria:
        if c in prompt or c.lower() in prompt.lower():
            criteria_results.append(f"  - {c}: 已覆盖")
        else:
            criteria_results.append(f"  - {c}: 未覆盖，建议补充")
            issues.append(f"缺少'{c}'相关内容")

    result = f"评分：{score}/10\n"
    if criteria_results:
        result += "评估标准：\n" + "\n".join(criteria_results) + "\n"
    if issues:
        result += "改进点：\n" + "\n".join(f"  - {i}" for i in issues)
    else:
        result += "提示词质量良好，无明显改进点。"

    return result


@tool
def search_history(
    query: Annotated[str, "搜索关键词或问题描述"],
    top_k: Annotated[int, "返回结果数量"] = 3,
) -> str:
    """搜索历史优化记录，查找类似需求的优化案例。当需要参考过往优化经验时调用此工具。"""
    from lyra4d.storage.local_db import get_db
    db = get_db()
    records = db.get_all()

    scored = []
    q_lower = query.lower()
    for r in records:
        score = 0
        if q_lower in r.get("user_input", "").lower():
            score += 2
        if q_lower in r.get("final_prompt", "").lower():
            score += 1
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return "未找到相关历史记录"

    results = []
    for _, r in scored[:top_k]:
        results.append(
            f"[需求] {r.get('user_input', '')}\n"
            f"[平台] {r.get('target_ai', '')}\n"
            f"[评分] {r.get('final_score', 0)}/10\n"
            f"[提示词摘要] {r.get('final_prompt', '')[:200]}..."
        )
    return "\n\n---\n\n".join(results)


# 平台适配知识库
PLATFORM_TIPS = {
    "chatgpt": """ChatGPT/GPT-4 平台适配建议：
- 使用 System 指令设定角色效果最佳
- 结构化章节（用 Markdown 标题分隔）能提升理解
- 对话引导式提示词效果好（如"让我先确认一下..."）
- 支持 function calling，可绑定外部工具
- 适合：结构化任务、代码生成、数据分析""",

    "claude": """Claude 平台适配建议：
- 长上下文支持（200K tokens），适合处理长文档
- XML 标签分隔效果好（如 <instructions>...</instructions>）
- 推理框架提示词效果佳（先分析再回答）
- 角色设定要具体，Claude 对角色理解很深
- 适合：深度分析、写作、复杂推理""",

    "gemini": """Gemini 平台适配建议：
- 创意任务表现优秀，适合头脑风暴
- 对比分析能力强，给它多个选项让它比较
- 多模态理解（图片+文字），适合视觉相关任务
- 提示词可以稍微开放一些，给它发挥空间
- 适合：创意写作、多模态任务、对比分析""",

    "deepseek": """DeepSeek 平台适配建议：
- 中文理解能力优秀，中文提示词直接写即可
- 推理能力强，适合技术类和逻辑推理任务
- 提示词建议用简洁直接的指令，避免过于复杂的嵌套结构
- 思维链（Chain-of-Thought）效果好，加一句"让我们一步步思考"
- 适合：代码生成、数学推理、技术文档、中文写作""",

    "doubao": """豆包（Doubao）平台适配建议：
- 中文自然语言生成非常流畅，口语化表达效果好
- 角色设定要清晰明确（如"你是一个专业的xxx"）
- 输出格式要具体（如"用列表形式回答"、"分3点说明"）
- 创意写作和日常对话表现优秀
- 提示词不宜过长，保持简洁明了
- 适合：日常对话、创意写作、营销文案、社交媒体内容""",
}


@tool
def get_platform_tips(
    platform: Annotated[str, "目标平台名称，如 chatgpt、claude、gemini、deepseek、doubao"],
) -> str:
    """获取指定 AI 平台的提示词适配建议。当需要针对特定平台优化提示词时调用此工具。"""
    key = platform.lower().strip()
    if key in PLATFORM_TIPS:
        return PLATFORM_TIPS[key]
    else:
        available = ", ".join(PLATFORM_TIPS.keys())
        return f"未找到'{platform}'的适配建议。支持的平台：{available}"


@tool
def search_knowledge(
    query: Annotated[str, "搜索关键词或问题描述"],
    top_k: Annotated[int, "返回结果数量"] = 3,
) -> str:
    """从知识库中检索与查询最相关的模板、平台适配建议和历史优化案例。
    当需要寻找参考模板、了解平台特性或参考历史优化时调用此工具。"""
    from lyra4d.rag.retriever import retrieve_templates
    return retrieve_templates(query, top_k)
