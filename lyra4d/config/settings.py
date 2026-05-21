from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Embedding 配置（阿里百炼）
    embedding_api_key: str = ""
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v3"

    # RAG 配置
    rag_top_k: int = 3

    # 迭代配置
    max_iterations: int = 2
    score_threshold: int = 7

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 日志配置
    log_level: str = "INFO"

    # 存储配置
    data_dir: str = "data"
    chroma_dir: str = "chroma_db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
