"""API 路由定义。"""

import uuid
import traceback
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from lyra4d.schemas.models import OptimizeRequest, OptimizeResult
from lyra4d.graph.workflow import get_workflow
from lyra4d.storage.local_db import get_db
from lyra4d.utils.logger import logger

router = APIRouter(prefix="/api", tags=["优化接口"])


def _extract_interrupt(result: dict) -> dict | None:
    """从结果中提取 interrupt 信息（兼容 __interrupt__ 返回值）。"""
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    interrupt_obj = interrupts[0]
    return interrupt_obj.value if hasattr(interrupt_obj, "value") else interrupt_obj


@router.post("/optimize")
async def optimize(req: OptimizeRequest):
    """优化接口（支持人类介入）。"""
    workflow = get_workflow()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "user_input": req.user_input,
        "mode": req.mode,
        "target_ai": req.target_ai,
    }

    try:
        result = await workflow.ainvoke(initial_state, config)
    except Exception as e:
        logger.error(f"[API] /optimize 异常: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {type(e).__name__}: {str(e)}")

    # 检查是否被 interrupt
    interrupt_value = _extract_interrupt(result)
    if interrupt_value:
        return {
            "status": "interrupted",
            "thread_id": thread_id,
            "draft": interrupt_value.get("draft", ""),
            "score": interrupt_value.get("score", 0),
            "improvement_points": interrupt_value.get("improvement_points", []),
            "message": interrupt_value.get("message", "请审阅并给出反馈"),
        }

    db = get_db()
    record = {
        "user_input": req.user_input,
        "mode": req.mode,
        "target_ai": req.target_ai,
        "final_prompt": result.get("final_prompt", ""),
        "final_score": result.get("final_score", 0),
        "total_iterations": result.get("total_iterations", 0),
        "optimization_summary": result.get("optimization_summary", "") or result.get("d4_result", {}).get("optimization_summary", ""),
        "usage_tips": result.get("usage_tips", "") or result.get("d4_result", {}).get("usage_tips", ""),
    }
    db.save(record)

    return {"status": "completed", **record}


@router.post("/optimize/resume")
async def optimize_resume(thread_id: str, feedback: str):
    """恢复被 interrupt 暂停的优化流程。"""
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await workflow.ainvoke(Command(resume=feedback), config)
    except Exception as e:
        logger.error(f"[API] /optimize/resume 异常: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"工作流恢复失败: {type(e).__name__}: {str(e)}")

    # 检查是否再次被 interrupt
    interrupt_value = _extract_interrupt(result)
    if interrupt_value:
        return {
            "status": "interrupted",
            "thread_id": thread_id,
            "draft": interrupt_value.get("draft", ""),
            "score": interrupt_value.get("score", 0),
            "improvement_points": interrupt_value.get("improvement_points", []),
            "message": interrupt_value.get("message", "请审阅并给出反馈"),
        }

    db = get_db()
    record = {
        "final_prompt": result.get("final_prompt", ""),
        "final_score": result.get("final_score", 0),
        "total_iterations": result.get("total_iterations", 0),
        "optimization_summary": result.get("optimization_summary", "") or result.get("d4_result", {}).get("optimization_summary", ""),
        "usage_tips": result.get("usage_tips", "") or result.get("d4_result", {}).get("usage_tips", ""),
    }
    db.save(record)

    return {"status": "completed", **record}


@router.get("/history")
async def history():
    """获取历史记录。"""
    db = get_db()
    return db.get_all()
