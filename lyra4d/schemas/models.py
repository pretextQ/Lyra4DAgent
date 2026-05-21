"""Pydantic 数据模型。"""

from typing import Optional
from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    """用户提交的优化请求。"""
    user_input: str = Field(..., description="用户的原始需求描述")
    mode: str = Field(default="detail", description="优化模式：detail / basic")
    target_ai: str = Field(default="general", description="目标 AI 平台：ChatGPT / Claude / Gemini / DeepSeek / 豆包 / 通用")


class D1Output(BaseModel):
    """D1 Define Agent 的输出：需求解析结果。"""
    core_intent: str = Field(description="用户的核心目标，一句话概括")
    key_entities: list[str] = Field(description="从需求中提取的关键概念、技术、平台等")
    context: str = Field(description="需求的背景、场景、约束条件")
    output_requirements: str = Field(description="用户期望的输出格式、风格、长度等")
    missing_info: list[str] = Field(description="需求中模糊或缺失，需要补充的信息")
    complexity: str = Field(description="需求复杂度评估：simple / medium / complex")


class D2Output(BaseModel):
    """D2 Design Agent 的输出：方案设计结果。"""
    optimization_techniques: list[str] = Field(description="选择的优化技术，如思维链、少样本、多视角分析等")
    prompt_framework: str = Field(description="提示词的整体框架结构，包含哪些部分")
    role_definition: str = Field(description="给 AI 设定的角色和专业领域")
    prompt_adaptation: str = Field(description="针对目标平台的适配策略")
    expected_output: str = Field(description="优化后预期能达到的效果")


class D3Output(BaseModel):
    """D3 Develop Agent 的输出：迭代开发结果。"""
    current_draft: str = Field(description="本轮生成的提示词草稿")
    score: int = Field(description="当前草稿的自评分数，1-10 分")
    improvement_points: list[str] = Field(description="当前草稿的改进点列表")
    iteration: int = Field(description="当前迭代轮次")


class D4Output(BaseModel):
    """D4 Deliver Agent 的输出：最终交付结果。"""
    final_prompt: str = Field(description="最终生成的提示词")
    optimization_summary: str = Field(description="优化总结：改了什么、为什么这么改")
    usage_tips: str = Field(description="使用提示词的技巧和注意事项")


class OptimizeResult(BaseModel):
    """优化结果的完整响应。"""
    final_prompt: str = Field(description="最终生成的提示词")
    optimization_summary: str = Field(description="优化总结：改了什么、为什么这么改")
    usage_tips: str = Field(description="使用提示词的技巧和注意事项")
    core_intent: str = Field(description="用户核心目标，一句话概括")
    total_iterations: int = Field(description="总共迭代了多少轮")
    final_score: int = Field(description="最终评分，1-10 分")



class SSEEvent(BaseModel):
    """SSE 流式事件。"""
    event_type: str = Field(description="事件类型")
    agent_name: str = Field(description="事件对应的 Agent 名称")
    message: str = Field(description="事件内容")
    data: Optional[dict] = Field(description="事件数据")
