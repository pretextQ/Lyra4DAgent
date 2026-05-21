"""ChromaDB 数据灌入脚本。

运行方式：uv run python -m lyra4d.rag.seed
"""

import json
import os
from lyra4d.rag.vector_store import get_vector_store
from lyra4d.utils.logger import logger


# ---- 模板数据（与 mcp/server.py 中一致） ----
TEMPLATES = {
    "邮件写作模板": "你是一位专业的商务邮件撰写者。请根据以下信息撰写邮件：收件人、主题、要点。要求语气专业、结构清晰。",
    "代码审查模板": "你是一位资深代码审查工程师。请审查以下代码，关注：安全性、性能、可读性。给出具体的改进建议。",
    "营销文案模板": "你是一位创意营销文案专家。请根据产品特点撰写营销文案，突出卖点，吸引目标用户。",
    "数据分析模板": "你是一位数据分析师。请分析以下数据，找出关键趋势和异常值，给出可执行的建议。",
}

# ---- 平台适配建议（与 utils/agent_tools.py 中一致） ----
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


def _sanitize_id(name: str) -> str:
    """将名称转为合法的 ChromaDB ID。"""
    return name.replace(" ", "_").replace("/", "_")


def _load_history(data_dir: str = "data") -> list[dict]:
    """加载历史优化记录。"""
    file_path = os.path.join(data_dir, "history.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed() -> None:
    """执行数据灌入。"""
    store = get_vector_store()

    documents = []
    metadatas = []
    ids = []

    # 模板
    for name, content in TEMPLATES.items():
        documents.append(content)
        metadatas.append({"category": "template", "name": name})
        ids.append(f"template_{_sanitize_id(name)}")

    # 平台适配
    for platform, tips in PLATFORM_TIPS.items():
        documents.append(tips)
        metadatas.append({"category": "platform_tip", "platform": platform})
        ids.append(f"tip_{platform}")

    # 历史记录
    history = _load_history()
    for record in history:
        final_prompt = record.get("final_prompt", "")
        if not final_prompt:
            continue
        documents.append(final_prompt)
        metadatas.append({
            "category": "history",
            "user_input": record.get("user_input", ""),
            "target_ai": record.get("target_ai", ""),
            "score": str(record.get("final_score", 0)),
        })
        ids.append(f"history_{record.get('id', '')}")

    if not documents:
        logger.warning("[Seed] 没有数据需要灌入")
        return

    store.add_documents(documents, metadatas, ids)
    history_count = len(ids) - len(TEMPLATES) - len(PLATFORM_TIPS)
    logger.info(f"[Seed] 完成！共灌入 {len(documents)} 条数据")
    print(f"[OK] Seed 完成：{len(documents)} 条数据已写入 ChromaDB")
    print(f"   - 模板: {len(TEMPLATES)} 条")
    print(f"   - 平台适配: {len(PLATFORM_TIPS)} 条")
    print(f"   - 历史记录: {history_count} 条")


if __name__ == "__main__":
    seed()
