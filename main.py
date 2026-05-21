"""Lyra4D Agent 入口文件。"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph")

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    print("🚀 Lyra4D Agent 启动中...")

    # 预热 RAG 知识库
    try:
        from lyra4d.rag.vector_store import get_vector_store
        store = get_vector_store()
        collection = store.get_or_create_collection()
        count = collection.count()
        print(f"📚 RAG 知识库已就绪，共 {count} 条知识")
    except Exception as e:
        print(f"⚠️ RAG 知识库初始化警告: {e}")

    yield
    print("👋 Lyra4D Agent 已停止")


app = FastAPI(
    title="Lyra4D Agent",
    description="基于 Lyra 4D 方法论的多 Agent 提示词智能优化系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径。"""
    return {
        "name": "Lyra4D Agent",
        "version": "0.1.0",
        "description": "多 Agent 提示词智能优化系统",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok"}


from lyra4d.api.routes import router
app.include_router(router)


def main():
    """启动服务。"""
    print("📡 服务启动于 http://0.0.0.0:8000")
    print("📖 API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
