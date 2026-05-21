"""快速测试：运行完整 workflow，验证统一 Agent 链路是否通畅。"""

import sys
import uuid
import asyncio
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langgraph.types import Command
from lyra4d.graph.workflow import get_workflow


async def main():
    workflow = get_workflow()

    initial_state = {
        "user_input": "帮我写一封产品发布邮件",
        "mode": "detail",
        "target_ai": "ChatGPT",
    }

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print("=" * 50)
    print("开始运行 Lyra4D 统一 Agent...")
    print("=" * 50)

    # 首次调用
    result = await workflow.ainvoke(initial_state, config)

    # 处理 interrupt 循环
    while "__interrupt__" in result:
        interrupts = result["__interrupt__"]
        if not interrupts:
            break
        interrupt_value = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]

        print(f"\n[Interrupt] Agent 请求用户反馈")
        print(f"  草稿评分: {interrupt_value.get('score', '?')}/10")
        print(f"  改进点: {interrupt_value.get('improvement_points', [])}")
        draft_preview = str(interrupt_value.get('draft', ''))[:100]
        print(f"  草稿预览: {draft_preview}...")

        # 模拟用户输入"通过"
        print(f"\n[Resume] 发送用户反馈: '通过'")
        result = await workflow.ainvoke(Command(resume="通过"), config)

    print("\n" + "=" * 50)
    print("运行结果：")
    print("=" * 50)
    print(f"最终提示词：\n{result.get('final_prompt', '无')}")
    print(f"\n最终评分：{result.get('final_score', '无')}")
    print(f"总迭代次数：{result.get('total_iterations', '无')}")
    print(f"\n优化总结：{result.get('optimization_summary', '无')}")
    print(f"\n使用技巧：{result.get('usage_tips', '无')}")


if __name__ == "__main__":
    asyncio.run(main())
