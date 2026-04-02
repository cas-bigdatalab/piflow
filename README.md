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
flow-deepagents/
├── main_cli.py                     # CLI 启动入口
│
├── agents/                         # Agent 封装与编排
│   ├── factory.py                  # AgentFactory: 组装 deepagents Agent（model/prompt/tools/memory）
│   ├── prompts.py                  # 系统提示词模板（BASE_PROMPT、WORKSPACE_PROMPT、build_system_prompt）
│   ├── middleware.py               # registry hooks（before/after tool call 日志记录）
│   └── tools.py                    # 内置工具（exec_shell 执行终端命令）
│
├── api/                            # API 服务
│   └── server.py                   # FastAPI 服务启动入口
│
├── runtime/                        # 运行编排层
│   ├── engine.py                   # 主运行入口：初始化 -> 创建 agent -> run
│   ├── policy.py                   # 安全策略/预算控制
│   ├── skill_loader.py             # 本地 skills 加载器
│   ├── workspace_manager.py        # workspace 生命周期管理
│   └── events.py                   # 事件总线（tool_called/tool_finished 等）
│
├── tools/                          # 工具统一抽象层
│   ├── core/
│   │   ├── base.py               # ToolSpec / ToolResult 定义
│   │   ├── registry.py           # ToolRegistry：注册、查找、执行工具
│   │   └── naming.py             # namespace.tool_name 规范
│   └── adapters/
│       ├── deepagents_adapter.py # ToolSpec -> deepagents tool format
│       └── mcp_adapter.py        # MCP Tool -> ToolSpec
│
├── mcp_runtime/                    # MCP 管理中心
│   ├── mcp_runtime.py            # MCP runtime 主入口
│   ├── client_manager.py         # MCP client 生命周期
│   ├── mcp_registry_loader.py    # MCP tools 注册到 registry
│   ├── health_monitor.py         # MCP 服务健康检测
│   ├── reconnect_loop.py         # 自动重连
│   └── schema_cache.py          # 防止重复加载 tools
│
├── infra/                          # 基础设施
│   ├── config_loader.py          # 配置加载（yaml）
│   ├── env_loader.py             # .env 文件加载
│   ├── logging.py                # 日志初始化
│   └── settings.py               # 配置模型定义
│
├── config/                         # 配置文件
│   ├── app.yaml                  # 应用配置
│   ├── llm.yaml                  # LLM 配置
│   ├── mcp_servers.yaml          # MCP 服务列表
│   └── skills.yaml               # skills 配置
│
├── workspace/                      # Agent 工作目录
│   ├── artifacts/                # 任务产物
│   ├── outputs/                  # 结果文件
│   ├── temp/                     # 临时文件
│   ├── logs/                     # 日志
│   └── skills/                    # skills 目录
│
├── test/                           # 测试
│   ├── test_registry.py          # registry 单元测试
│   ├── test_deepagents_adapter.py # adapter 测试
│   └── ...
│
├── README.md
└── requirements.txt
```
