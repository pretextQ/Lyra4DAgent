"""RAG 检索器。"""

from lyra4d.rag.vector_store import get_vector_store
from lyra4d.config.settings import get_settings
from lyra4d.utils.logger import logger

CATEGORY_LABELS = {
    "template": "模板",
    "platform_tip": "平台适配",
    "history": "历史案例",
}


def retrieve_templates(query: str, top_k: int | None = None) -> str:
    """检索与需求最相关的知识，返回拼接好的上下文字符串。"""
    settings = get_settings()
    k = top_k or settings.rag_top_k
    store = get_vector_store()

    try:
        results = store.query(query, top_k=k)
    except Exception as e:
        logger.warning(f"[RAG] 检索失败: {e}")
        return "未找到相关知识"

    if not results:
        return "未找到相关知识"

    parts = []
    for r in results:
        category = r["metadata"].get("category", "")
        label = CATEGORY_LABELS.get(category, category)
        name = r["metadata"].get("name") or r["metadata"].get("platform") or r["metadata"].get("user_input", "")
        header = f"[{label}] {name}".strip()
        parts.append(f"{header}\n{r['document']}")

    return "\n\n---\n\n".join(parts)
