"""LLM 调用工具。"""

import json
import asyncio
from typing import TypeVar, Type
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from lyra4d.config.settings import get_settings
from lyra4d.utils.logger import logger

T = TypeVar("T", bound=BaseModel)


class AgentOutputError(Exception):
    """Agent 输出解析失败（重试耗尽后抛出）。"""
    pass


def create_llm(temperature: float = 0.3) -> ChatOpenAI:
    """创建 LLM 实例。

    ChatOpenAI 兼容所有 OpenAI 格式的 API（DeepSeek、豆包、OpenAI 等），
    只要改 base_url 和 model 就能切换模型。
    """
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
    )


async def call_llm_with_retry(
    agent_name: str,
    system_prompt: str,
    human_msg: str,
    output_model: Type[T],
    temperature: float = 0.3,
    max_retries: int = 2,
) -> T:
    """统一的 Agent LLM 调用。优先用 with_structured_output，失败则手动解析 JSON。"""
    llm = create_llm(temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    try:
        structured_llm = llm.with_structured_output(output_model)
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"[{agent_name}] 第{attempt + 1}次调用 LLM（structured）...")
                result = await structured_llm.ainvoke(messages)
                logger.info(f"[{agent_name}] 调用成功")
                return result
            except Exception as e:
                logger.warning(f"[{agent_name}] 第{attempt + 1}次调用失败: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
        raise AgentOutputError(f"{agent_name} 调用失败，已重试{max_retries}次")
    except AgentOutputError:
        raise
    except Exception:
        logger.info(f"[{agent_name}] 模型不支持 with_structured_output，使用手动 JSON 解析")


    schema_fields = ", ".join(output_model.model_fields.keys())
    format_instruction = f"\n请严格以 JSON 格式输出，只包含以下字段：{schema_fields}\n不要输出任何其他内容，只输出 JSON。"
    full_system = system_prompt + format_instruction

    messages = [
        SystemMessage(content=full_system),
        HumanMessage(content=human_msg),
    ]

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[{agent_name}] 第{attempt + 1}次调用 LLM...")
            response = await llm.ainvoke(messages)
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            schema = output_model.model_fields
            for key, value in data.items():
                if key in schema and schema[key].annotation == str and not isinstance(value, str):
                    data[key] = json.dumps(value, ensure_ascii=False)

            result = output_model(**data)
            logger.info(f"[{agent_name}] 调用成功")
            return result
        except Exception as e:
            logger.warning(f"[{agent_name}] 第{attempt + 1}次调用失败: {e}")
            if attempt < max_retries:
                await asyncio.sleep(1)

    raise AgentOutputError(f"{agent_name} 调用失败，已重试{max_retries}次")
