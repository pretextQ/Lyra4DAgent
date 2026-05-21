# LangGraph Agent 学习路线图（基于 Lyra4D 项目）

> 目标：边学边改 Lyra4D 项目，学完即拥有一个可拿得出手的 Agent 项目
> 项目路径：D:\python_files\LyraPrompt

---

## 阶段一：LangGraph 基础入门

> 对应项目文件：`graph/workflow.py`、`state/graph_state.py`、`schemas/models.py`
> 目标：看懂项目现有的图是怎么搭的，能自己从零写一个

**1.1 LangGraph 核心概念**
- LangGraph 是什么：基于有向图的 Agent 编排框架，核心解决"循环 + 状态 + 可控"三个问题
- LangGraph vs LangChain Chains：Chains 只能线性执行，Graph 支持循环和分支；Chain 隐式传状态，Graph 显式管理状态
- LangGraph vs AutoGPT：LangGraph 你来控制流程，AutoGPT 自己决定一切（黑盒不可控）
- LangGraph 0.2+ 关键变化：StateGraph 替代 Graph、MessagesState 成标准、ToolNode 重构、CheckpointSaver 统一
- 项目映射：`graph/workflow.py:213` 的 `build_workflow()` 就是一个完整的 StateGraph 构建过程

**1.2 三大核心概念**
- **状态(State)**：Agent 的全局共享内存，所有节点通过它传递数据
  - 项目映射：`state/graph_state.py` 的 `GraphState(TypedDict)` 就是状态定义
  - 学习点：TypedDict 定义状态、字段类型注解、可选字段（Optional）
- **节点(Node)**：图的执行单元，输入状态 → 处理 → 返回状态更新
  - 项目映射：`graph/workflow.py:22` 的 `node_d1` 就是一个节点函数
  - 学习点：节点函数签名必须是 `(state) -> dict`，返回值是状态的增量更新
- **边(Edge)**：连接节点，定义执行顺序和分支逻辑
  - 项目映射：`graph/workflow.py:228-241` 有普通边 `add_edge` 和条件边 `add_conditional_edges`
  - 学习点：普通边（顺序执行）、条件边（分支逻辑）、循环边（条件边实现循环）

**1.3 状态管理深入**
- TypedDict 状态（简单场景）
  - 项目映射：`state/graph_state.py` 就是用 TypedDict
  - 学习点：字段定义、嵌套类型（list、dict）、默认值
- Pydantic BaseModel 状态（需要校验的场景）
  - 学习点：Pydantic 状态定义、Field 验证器、默认值与默认工厂、嵌套模型
  - 项目映射：`schemas/models.py` 里的 D1Output、D2Output 等就是 Pydantic 模型，可以试着把 GraphState 也改成 Pydantic
- 状态更新机制
  - 合并更新：字典深度合并、列表自动追加
  - 覆盖更新：完全替换指定字段
  - 项目映射：`graph/workflow.py:156` 节点返回 `{"d3_result": result, "current_iteration": iteration}` 就是状态更新

**1.4 节点定义与执行**
- 同步节点 `def` vs 异步节点 `async def`
  - 项目映射：项目所有节点都是 `async def`，因为要调异步 LLM
- 节点中调用大模型
  - 项目映射：`utils/llm_helper.py:56` 的 `create_llm()` 和 `utils/llm_helper.py:67` 的 `call_llm_with_retry()`
  - 学习点：ChatOpenAI 初始化、消息格式（SystemMessage/HumanMessage）、temperature 等参数
- 返回值必须为字典格式
  - 项目映射：每个节点函数都返回 dict，如 `return {"d1_result": result}`

**1.5 边与控制流**
- **普通边**：`add_edge(src, dst)` 顺序执行
  - 项目映射：`graph/workflow.py:229` `workflow.add_edge("d0_welcome", "d1_define")`
- **条件边**：`add_conditional_edges(src, condition_fn, mapping)` 分支逻辑
  - 项目映射：`graph/workflow.py:234-241` D3 节点的条件分支（继续迭代 or 交付）
  - 学习点：条件函数返回字符串、字符串到节点名的映射字典
- **循环边**：用条件边实现，配合递归限制
  - 项目映射：D3 的迭代循环就是条件边实现的
  - 学习点：循环终止条件设计、循环计数器、recursive_limit
- **START / END 特殊节点**
  - 项目映射：`graph/workflow.py:228` `set_entry_point`、`graph/workflow.py:243` `add_edge("d4_deliver", END)`

**1.6 图的编译与执行**
- **编译流程**：`StateGraph` → `compile()` → `CompiledGraph`
  - 项目映射：`graph/workflow.py:245` `return workflow.compile()`
- **执行方法**：`invoke()` 同步、`ainvoke()` 异步
  - 项目映射：`api/routes.py:41` `await workflow.ainvoke(initial_state)`
  - 学习点：输入参数格式、执行配置(config)、返回值结构
- **图可视化**：`draw_mermaid_png()` 生成流程图
  - 学习点：Mermaid 图语法、调试技巧

**1.7 环境搭建与工具链**
- UV 包管理器安装与使用
  - 项目映射：`pyproject.toml` + `uv.lock` 就是 UV 管理的
  - 学习点：`uv init`、`uv add`、`uv sync`、`uv lock` 命令
- LangSmith 配置（调试追踪）
  - 学习点：环境变量配置、执行流程可视化、节点输入输出查看
- python-dotenv 环境变量管理
  - 项目映射：`config/settings.py` 用 pydantic-settings 读 .env

---

## 阶段二：核心组件深入

> 对应项目改造：给项目加上真正的 Agent 能力
> 目标：理解 LangGraph 的高级特性，开始把项目从 Pipeline 升级为 Agent

**2.1 MessagesState（替代自定义 TypedDict）**
- MessagesState 预定义结构：自带 `messages` 字段，自动追加
- 支持的消息类型：HumanMessage、AIMessage、ToolMessage、SystemMessage
- MessagesState vs 自定义 TypedDict 的选择
- 扩展 MessagesState 添加自定义字段
- 实践：把 `state/graph_state.py` 的 TypedDict 改成 MessagesState 或继承它

**2.2 ToolNode 内置节点**
- ToolNode 核心作用：自动解析 AIMessage 中的工具调用并执行
- 工具调用结果自动转换为 ToolMessage
- 多工具并行执行
- 工具执行错误自动处理
- 实践：给项目加上第一个 ToolNode（比如"搜索提示词模板"工具）

**2.3 状态持久化与 CheckpointSaver**
- CheckpointSaver 核心原理：每次节点执行后保存状态快照
- SqliteSaver 本地文件持久化
- PostgreSQLSaver 分布式持久化
- 指定 checkpoint_id 恢复执行
- 状态版本控制与历史回溯
- 断点续执行实现
- 实践：给项目加上 CheckpointSaver，让优化中断后能恢复

**2.4 流式输出（stream 方法）**
- `stream()` 基础使用
- 节点级流式输出（values、updates 模式）
- 令牌级流式输出（messages 模式）
- 异步流式输出 `astream()`
- 项目映射：项目目前用 SSE 自己实现了一套流式，但没用 LangGraph 原生的 stream()
- 实践：用 `workflow.astream()` 替代手动 SSE

**2.5 并行节点执行**
- `add_edge()` 同时指向多个节点
- 并行节点状态合并策略
- 并行执行的线程安全
- 实践：让 D1（需求解析）和 RAG 检索并行执行

**2.6 执行配置详解**
- `recursive_limit`：递归深度限制（防死循环）
- `timeout`：全局执行超时
- `max_concurrency`：最大并发数
- `configurable`：自定义配置项
- 项目映射：可以给 workflow.ainvoke 传 config 控制这些参数

**2.7 图可视化**
- `draw_mermaid_png()` 方法
- Mermaid 图语法生成
- 图结构导出为图片
- 实践：给项目加一个 `/api/workflow/graph` 接口返回流程图

---

## 阶段三：工具调用核心技术

> 这是从 Pipeline 变成 Agent 的关键转折点！
> 目标：让 Agent 能使用工具，实现"思考 → 行动 → 观察"循环

**3.1 大模型工具调用原理**
- 工具调用协议标准：函数定义 JSON Schema
- 模型工具选择逻辑：LLM 根据上下文决定调用哪个工具
- 工具调用响应格式：AIMessage 中的 tool_calls 字段
- 多轮工具调用流程：思考 → 调用工具 → 看结果 → 继续思考

**3.2 @tool 装饰器**
- 基本语法与工具命名
- 工具描述编写规范（影响 LLM 选择工具的准确度）
- 参数类型注解要求（str、int、list、Enum、Pydantic 模型）
- 参数描述：Annotated + docstring
- 异步工具定义
- 实践：写几个工具
  - `search_templates(query: str)` - 搜索提示词模板
  - `evaluate_prompt(prompt: str, criteria: list[str])` - 评估提示词质量
  - `get_platform_tips(platform: str)` - 获取平台适配建议

**3.3 bind_tools 工具绑定**
- 将工具绑定到 ChatModel
- 同时绑定多个工具
- `tool_choice` 参数：强制/自动/禁止使用工具
- `parallel_tool_calls`：是否允许并行调用
- 实践：`llm.bind_tools([search_templates, evaluate_prompt])`

**3.4 ToolNode 执行逻辑**
- 从 AIMessage 中解析 tool_calls
- 工具实例化与参数传递
- 执行结果转换为 ToolMessage
- 多工具并行执行
- 工具执行异常捕获
- 实践：在 workflow 中加入 ToolNode，替换手动工具调用

**3.5 ReAct 循环实现（Agent 核心！）**
- ReAct 核心思想：推理(Reasoning) + 行动(Acting) 交替
- 标准流程：LLM 思考 → 决定调用工具 → 执行工具 → 观察结果 → 继续思考
- LangGraph 中的 ReAct 实现：`should_continue` 检查是否有 tool_calls
- 实践：改造 D3 节点，让它成为真正的 ReAct Agent
  ```
  D3 节点（LLM）→ 有 tool_calls？→ 是 → ToolNode → 回到 D3 节点
                                        → 否 → 返回结果
  ```

**3.6 工具调用高级话题**
- 工具调用重试机制与指数退避
- 工具调用超时处理
- 结构化工具输出（Pydantic 作为返回值）
- 工具权限控制（白名单、次数限制）
- 工具调用审计与日志
- 自定义工具开发规范
- 实践：给工具加超时、重试、日志

**3.7 结构化输出**
- `with_structured_output()` 方法
- 用 Pydantic 模型约束 LLM 输出
- 替代手动 JSON 解析
- 项目映射：`utils/llm_helper.py` 里手动解析 JSON + 重试的逻辑，可以用 `with_structured_output` 替代
- 实践：重构 `call_llm_with_retry`，用 `llm.with_structured_output(D1Output)` 替代手动解析

---

## 阶段四：MCP 协议集成

> 让 Agent 能连接外部服务，扩展能力边界

**4.1 MCP 协议基础**
- MCP 全称：Model Context Protocol
- 解决的问题：工具调用的标准化、动态发现、跨语言跨平台
- 核心组件：MCP Server（提供工具）、MCP Client（消费工具）
- 通信机制：JSON-RPC 2.0、stdio/HTTP/WebSocket 传输层

**4.2 MCP 服务器开发**
- mcp 包安装与服务器初始化
- `@mcp.tool` 装饰器定义工具
- `@mcp.resource` 装饰器定义资源
- `@mcp.prompt` 装饰器定义提示模板
- 服务器配置与运行
- 实践：把 Lyra4D 的模板管理功能封装成 MCP 服务器

**4.3 LangGraph 中使用 MCP 工具**
- MCPClient 初始化与连接配置
- MCP 工具动态发现与加载
- 动态转换为 LangChain 工具
- MCP 工具绑定到模型 / ToolNode
- 多 MCP 服务器同时使用
- 实践：在 Agent 中接入一个现成的 MCP 服务器（如文件系统 MCP）

**4.4 常用 MCP 服务器**
- 文件系统 MCP：文件读写、目录操作
- 浏览器 MCP：网页导航、内容提取
- 数据库 MCP：SQL 查询
- 代码执行 MCP：Python 代码运行

---

## 阶段五：高级 Agent 架构

> 从单 Agent 升级为多 Agent 系统，这是项目的核心卖点

**5.1 单 Agent 模块化设计**
- 单一职责原则：每个 Agent 只做一件事
- 节点模块化拆分
- 工具模块化管理
- 项目映射：D1/D2/D3/D4 的设计已经符合单一职责，但需要加上工具能力

**5.2 多 Agent 协作模式**
- **监督者模式**（最常用）：一个 Agent 负责分配任务，其他 Agent 执行
  - 实践：加一个 Supervisor Agent，根据用户需求动态决定要走 D1→D4 全流程还是只走部分
- **顺序执行模式**：流水线式处理
  - 项目映射：当前项目就是这种模式（D1→D2→D3→D4）
- **并行执行模式**：独立子任务并行处理
  - 实践：D1 和 RAG 检索并行
- **分层架构模式**：高层决策 → 中层协调 → 低层执行
- **辩论模式**：多个 Agent 持不同观点，投票决策

**5.3 记忆系统**
- **短期记忆**：会话历史消息
  - 用 MessagesState 自动管理
  - 历史消息截断策略、上下文窗口管理
  - 消息摘要生成
- **长期记忆**：跨会话持久化
  - 向量数据库存储（项目已有 ChromaDB）
  - 记忆嵌入与检索
  - 实体记忆：关键实体提取与存储
- **记忆检索与更新策略**
  - 相似度检索、时间加权检索、重要性加权
  - 记忆遗忘机制
- 实践：让 Agent 记住用户之前的优化偏好

**5.4 人类介入（Human-in-the-loop）**
- 人类介入的核心价值：审核、纠错、决策
- `interrupt()` 中断机制：暂停执行等待人类输入
- `Command` 恢复机制：携带人类输入恢复执行
- 人类审核工具调用：在执行敏感工具前暂停
- 人类反馈与修正：纠正、补充、评分
- 异步人类介入：Webhook 回调、任务队列
- 实践：在 D3 迭代中加人类审核，用户可以给反馈让 Agent 改进

**5.5 Agent 评估**
- 核心指标：任务成功率、工具调用准确率、Token 使用量、用户满意度
- 评估数据集设计
- 自动评估 vs 人工评估
- A/B 测试设计
- 实践：给项目加一个评估模块，自动给优化结果打分

**5.6 预构建 Agent**
- `create_react_agent()` 一行代码创建 ReAct Agent
- 与手写图的对比：什么时候用预构建，什么时候手写
- 实践：用 `create_react_agent` 快速搭建一个原型，和手写版对比

---

## 阶段六：生产级部署与优化

> 让项目从"能跑"变成"能上线"

**6.1 异步与并发优化**
- 异步节点、异步模型调用、异步工具调用
- 并发工具调用
- 线程池/进程池配置
- 项目映射：项目已经用了 async/await，但可以优化并发执行

**6.2 企业级可靠性**
- 全局错误处理中间件
- 断路器模式（连续失败后停止调用）
- 幂等性设计
- 多层超时控制：请求级、节点级、工具级
- 指数退避重试
- 优雅关闭与资源释放
- 降级策略
- 实践：给 LLM 调用加上断路器、多层超时

**6.3 可观测性**
- LangSmith 深度使用：自定义追踪、标签、过滤
- 自定义业务指标收集
- Prometheus + Grafana 集成
- OpenTelemetry 分布式追踪
- Token 使用量统计与成本监控
- 实践：接入 LangSmith，给每次优化生成追踪链接

**6.4 性能优化**
- LLM 响应缓存（语义缓存 / 精确缓存）
- 工具调用结果缓存
- 提示词优化：减少 Token 使用
- 批处理优化
- 向量检索性能优化
- 实践：给相同需求的优化结果加缓存

**6.5 部署方式**
- FastAPI 部署
  - 项目映射：`main.py` 已经有 FastAPI，需要加固
  - 学习点：依赖注入、接口文档、错误处理
- Docker 容器化
  - Dockerfile 编写、多阶段构建、镜像优化
  - 实践：给项目写 Dockerfile
- 云服务部署：AWS ECS / Azure App Service / Google Cloud Run
- 无服务器部署：AWS Lambda、冷启动优化

**6.6 安全与合规**
- API 密钥安全管理
- 工具调用 RBAC 权限控制
- 输入输出内容安全检测
- PII 识别与脱敏
- 审计日志
- 实践：给 API 加认证、敏感信息脱敏

**6.7 高级特性**
- 子图(Subgraph)复用与组合
- 图的动态修改：运行时添加/删除节点和边
- 图的版本管理
- 多模态 Agent：图像、音频处理
- LangGraph Cloud 平台
- Functional API：`@entrypoint` / `@task` 新写法

---

## 实战项目迭代里程碑

> 每个阶段结束后，项目应该有可感知的进步

| 阶段 | 里程碑 | 关键变化 |
|------|--------|----------|
| 阶段一结束 | 能跑的 Pipeline | 看懂现有代码，能从零搭 StateGraph，能用 UV 管理环境 |
| 阶段二结束 | 流式 + 持久化 | MessagesState 管理对话，CheckpointSaver 断点续执行，stream() 替代手动 SSE |
| 阶段三结束 | 真正的 Agent | Agent 能使用工具，ReAct 循环，with_structured_output 替代手动 JSON 解析。**Pipeline → Agent 质变！** |
| 阶段四结束 | MCP 生态 | 接入外部 MCP 服务器，自己封装 MCP 服务器 |
| 阶段五结束 | 多 Agent 协作 | Supervisor Agent 动态调度，记忆系统，人类介入。**单 Agent → 多 Agent 系统！** |
| 阶段六结束 | 生产就绪 | Docker 容器化，LangSmith 追踪，安全加固，性能优化。**Demo → 可上线产品！** |
