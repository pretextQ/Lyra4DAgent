"""RAG 向量存储。"""

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from lyra4d.config.settings import get_settings
from lyra4d.utils.logger import logger


COLLECTION_NAME = "lyra_knowledge"


class VectorStore:
    """ChromaDB 向量存储封装。"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._embedding: OpenAIEmbeddings | None = None

    def _ensure_embedding(self) -> OpenAIEmbeddings:
        """懒加载 Embedding 模型。"""
        if self._embedding is None:
            settings = get_settings()
            self._embedding = OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.embedding_api_key,
                openai_api_base=settings.embedding_base_url,
                check_embedding_ctx_length=False,
                chunk_size=10,
            )
        return self._embedding

    def get_or_create_collection(self, name: str = COLLECTION_NAME):
        """获取或创建 collection。"""
        return self.client.get_or_create_collection(name=name)

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        """写入文档（外部计算 embedding 后传入 ChromaDB）。"""
        embedding = self._ensure_embedding()
        vectors = embedding.embed_documents(documents)
        collection = self.get_or_create_collection(collection_name)
        collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"[VectorStore] 写入 {len(documents)} 条文档到 '{collection_name}'")

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        where: dict | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> list[dict]:
        """语义查询，返回匹配结果列表。"""
        collection = self.get_or_create_collection(collection_name)
        if collection.count() == 0:
            return []

        embedding = self._ensure_embedding()
        query_vector = embedding.embed_query(query_text)

        kwargs = {
            "query_embeddings": [query_vector],
            "n_results": min(top_k, collection.count()),
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return output


# 全局实例
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例。"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
