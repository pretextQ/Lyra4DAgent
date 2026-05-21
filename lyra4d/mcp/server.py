"""Lyra4D MCP Server。

提供语义搜索模板、平台适配建议、历史记录查询等工具和资源。
启动前需先运行：uv run python -m lyra4d.rag.seed
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("lyra-tools")


# ---- 工具 ----

@mcp.tool()
def evaluate_prompt(prompt: str, criteria: list[str]) -> str:
    """评估提示词质量，返回评分和具体改进点。"""
    from lyra4d.utils.agent_tools import evaluate_prompt as _evaluate_prompt
    return _evaluate_prompt(prompt, criteria)


@mcp.tool()
def search_templates(query: str, top_k: int = 3) -> str:
    """搜索提示词模板库，返回和查询最相关的模板（语义搜索）。"""
    from lyra4d.rag.retriever import retrieve_templates
    return retrieve_templates(query, top_k)


@mcp.tool()
def get_platform_tips(platform: str) -> str:
    """获取指定 AI 平台的提示词适配建议。支持：chatgpt、claude、gemini、deepseek、doubao。"""
    from lyra4d.utils.agent_tools import PLATFORM_TIPS
    key = platform.lower().strip()
    if key in PLATFORM_TIPS:
        return PLATFORM_TIPS[key]
    available = ", ".join(PLATFORM_TIPS.keys())
    return f"未找到'{platform}'的适配建议。支持的平台：{available}"


@mcp.tool()
def search_history(query: str, top_k: int = 3) -> str:
    """搜索历史优化记录，查找类似需求的优化案例。"""
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


# ---- 资源 ----

@mcp.resource("templates://list")
def list_templates() -> str:
    """返回所有可用的模板类别说明。"""
    return (
        "可用模板类别：\n"
        "- 邮件写作模板：专业商务邮件撰写\n"
        "- 代码审查模板：安全性、性能、可读性审查\n"
        "- 营销文案模板：产品卖点营销文案\n"
        "- 数据分析模板：数据趋势与异常分析\n\n"
        "使用 search_templates 工具进行语义搜索获取具体内容。"
    )


@mcp.resource("platforms://list")
def list_platforms() -> str:
    """返回所有支持的 AI 平台列表。"""
    from lyra4d.utils.agent_tools import PLATFORM_TIPS
    return "\n".join(f"- {name}" for name in PLATFORM_TIPS.keys())


@mcp.resource("history://count")
def history_count() -> str:
    """返回历史优化记录数量。"""
    from lyra4d.storage.local_db import get_db
    db = get_db()
    records = db.get_all()
    return f"共 {len(records)} 条历史记录"


if __name__ == "__main__":
    mcp.run()
