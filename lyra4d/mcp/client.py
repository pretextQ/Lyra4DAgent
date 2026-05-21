"""MCP Client — 供外部 Agent 连接本项目 MCP Server 时参考。

本项目的 Agent 自身直接调用本地工具（lyra4d.utils.agent_tools），不走 MCP Client。
此文件的用途：
  1. 测试 MCP Server 是否正常工作
  2. 供其他 Agent（如 Claude Desktop、Cursor）连接时参考配置方式

使用示例：
    import asyncio
    from lyra4d.mcp.client import get_mcp_tools

    tools = asyncio.run(get_mcp_tools())
    for t in tools:
        print(t.name, t.description)
"""

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVER_CONFIG = {
    "lyra-tools": {
        "command": "python",
        "args": ["-m", "lyra4d.mcp.server"],
        "transport": "stdio",
    }
}


async def get_mcp_tools() -> list:
    """从 MCP Server 获取所有可用工具（LangChain BaseTool 格式）。"""
    client = MultiServerMCPClient(MCP_SERVER_CONFIG)
    tools = await client.get_tools()
    return tools
