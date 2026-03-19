# Flow DeepAgent Project

这是一个基于 **DeepAgents** 框架、**本地 Skills** 与 **多 MCP (Model Context Protocol) 客户端** 的智能体框架。
本项目通过统一工具抽象层，实现了复杂任务在本地环境与远程服务之间的无缝调度。
 pip install -qU deepagents
 pip install deepagents tavily-python


## 1.快速开始
### 1) 运行命令行 Agent
请先确保安装了所需的依赖库，并且增加.env文件，配置好你的 API Key。

```text
DASHSCOPE_API_KEY="******"
```

```bash
python main_cli.py
```

skill样例测试：我想先对temp/森林每木调查数据QC.csv数据集文件进行随机采样10%，再把随机采样的输出结果进行二次采样10% ；采样结果临时保存起来


### 2) 启动 API 服务（推荐）

```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload
```

### 3)  API 备用启动方式（不推荐）

```bash
python -m api.server
```

## 2. 项目目录结构

```text
deep-agent-project/
├── api/                         # 基于 deepagents 的 Agent 封装与编排
│   ├── server.py                # 服务启动入口
│
├── agents/                         # 基于 deepagents 的 Agent 封装与编排
│   ├── factory.py                  # create_agent(): 组装 deepagents Agent（model/prompt/tools/memory）
│   ├── prompts.py                  # 系统提示词/规划提示词模板（集中管理）
│   ├── middleware.py               # deepagents middleware hooks（before/after tool call、日志、审计）
│   ├── planner.py                  # 可选：Plan-and-Execute 规划器（只负责产出 plan，不负责循环执行）
│   └── deepagents_config.py        # 可选: backend / workspace / default settings
│
├── tools/                          # 工具统一抽象层（你项目核心价值）
│   ├── core/
│   │   ├── base.py               # ToolSpec / ToolRequest / ToolResult（统一协议）
│   │   ├── registry.py           # ToolRegistry：注册、查找、按 namespace 管理
│   │   └── naming.py             # namespace.tool_name 规范（避免命名冲突）
│   ├── adapters/                    # 关键：对接 deepagents / MCP 的适配器
│   │    ├── deepagents_adapter.py   # ToolSpec -> deepagents tool format（函数/JSON schema/回调）
│   │    └── mcp_adapter.py          # MCP Tool -> ToolSpec（把 MCP schema 转成统一工具协议）
│
├── skills/                         # 本地能力集 (Local Toolkits)
│   ├── shell/
│   │   ├── executor.py             # Shell 执行（异步/超时）
│   │   ├── sandbox.py              # 安全沙箱（白名单/过滤/权限）
│   │   └── tools.py                # 暴露成 ToolSpec（如 shell.exec, shell.which）
│   └── file/
│       ├── reader.py               # 文件读取实现
│       ├── manager.py              # 文件管理实现（ls/mkdir/rm-safe）
│       └── tools.py                # 暴露成 ToolSpec（如 file.read, file.write）
│
├── mcp_runtime/                    # MCP 管理中心（远程工具入口）
│   ├── __init__.py
│   ├── client_manager.py           # MCP client 生命周期
│   ├── health_monitor.py           # MCP 服务健康检测
│   ├── mcp_runtime.py              # MCP runtime 主入口
│   ├── reconnect_loop.py           # 自动重连
│   ├── schema_cache.py             # 防止重复加载 tools
│   └── tool_loader.py              # 从 MCP 拉取 tools -> 通过 mcp_adapter 转成 ToolSpec 并注册
│
│
├── runtime/                        # 运行编排层（不是自研 Agent loop）
│   ├── engine.py                   # 主运行入口：加载配置 -> 初始化 registry/mcp/skills -> 创建 deepagents agent -> run
│   ├── context.py                  # 任务级上下文（trace_id、budget、用户输入、审计信息）
│   ├── policy.py                   # 安全策略/预算控制（工具允许列表、调用次数、超时等）
│   ├── memory.py                   # 记忆接口（短期上下文 + 长期存储，可选向量库）
│   ├── skill_loader.py             # 本地工具加载
│   ├── workspace_manager.py        # workspace 生命周期管理
│   └── events.py                   # 事件定义（tool_called/tool_finished/plan_created 等）
│
├── infra/                          # 基础设施与运行支持
│   ├── config_loader.py            # 配置加载（支持 yaml/json/env）
│   ├── logging.py                  # 结构化日志初始化
│   ├── metrics.py                  # 指标统计（调用次数/耗时/错误率）
│   └── tracing.py                  # 链路追踪（OpenTelemetry 等）
│
├── config/
│   ├── app.yaml                    # 应用配置
│   ├── llm.yaml                    # LLM 配置（可选：多个 LLM 客户端）
│   ├── mcp_servers.yaml            # MCP 服务列表配置
│   ├── skills.yaml                 # skills 启用与参数配置
│   └── policy.yaml                 # 可选：安全策略配置
│
├── workspace/                         # Agent 工作目录（sandbox）
│   ├── artifacts/
│   ├── outputs/
│   ├── temp/
│   └── logs/
│
├── tests/
│   ├── test_registry.py            # unit -测试工具注册、查找功能
│   ├── test_deepagents_adapter.py  # unit -测试 Adapter 层是否正确把 ToolSpec 转换为 DeepAgents / LangChain Tool
│   ├── test_mcp_adapter.py         # 测试 mcp adapter 功能
│   ├── test_shell_sandbox.py       # 测试 shell sandbox 功能
│   ├── test_engine_load_skills.py  # integration-测试 skills 是否真的被加载
│   └── test_engine_smoke.py        # smoke-测试 AgentEngine 是否可以启动
│
├── main.py                         # 项目启动入口（调用 runtime/engine.py）
├── main_cli.py                     # 项目交互式CLI启动入口（调用 runtime/engine.py）
├── README.md
└── requirements.txt
```
