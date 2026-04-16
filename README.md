# πFlowAgent / Flow DeepAgent

基于 DeepAgents、FastAPI、 Skill 接入和 React 前端的科研数据处理原型系统。

## 功能概览

- 流式智能体对话：`/chat/stream`
- 历史会话管理：创建、切换、删除、加载消息
- 工作区文件管理：上传输入文件、下载输出文件
- 消息级附件：普通上传附件和示例预置附件都可显示并持久化
- 示例流水线：点击示例后新建会话并自动触发任务
- 技能中心：读取技能列表和分类信息

## 项目结构

```text
flow-deepagents-0408/
├── server.py                  # FastAPI 入口
├── main_cli.py                # CLI 入口
├── requirements.txt           # Python 依赖
├── README.md
├── docs/
│   └── workspace_file_api.md  # 工作区文件接口说明（需按当前实现理解）
├── config/
│   ├── app.yaml
│   ├── database.yaml
│   ├── llm.yaml
│   └── mcp_servers.yaml
├── infra/                     # 配置、日志、环境变量加载
├── runtime/                   # Agent 运行编排、会话存储、工作区管理
├── agents/                    # agent factory、prompt、middleware、tools
├── tools/                     # 工具抽象层和 adapter
├── mcp_runtime/               # MCP client 生命周期与注册
├── workspace/                 # 工作区根目录
├── storage/                   # FastAPI 静态挂载目录
├── test/                      # Python 测试
└── vue-web/
    ├── package.json
    ├── README.md
    └── src/
        ├── components/
        ├── lib/
        └── pages/
```

## 运行前准备

### 1. Python 环境

建议使用 Python 3.10+。

安装依赖：

```bash
pip install -r requirements.txt
```

如果需要更稳定的 PostgreSQL 驱动编译环境，请提前安装本机对应的构建依赖。

### 2. Node 环境

前端建议使用 Node.js 18+。

```bash
cd vue-web
npm install
```

### 3. 数据库

项目使用 PostgreSQL 保存：

- 会话线程
- 聊天消息
- 消息附件记录
- 技能元数据

首次启动后端时会自动建表，但你需要先准备好数据库实例，并填写 [config/database.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/database.yaml)。

示例：

```yaml
host: "127.0.0.1"
port: 5432
user: "postgres"
password: "123456"
name: "flow_agent"
```

### 4. LLM 与环境变量

项目会从配置和环境变量中读取模型提供方参数。

需要关注：

- [config/llm.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/llm.yaml)
- `.env` 中的 provider API key

常见示例：

```bash
DASHSCOPE_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### 5. 可选依赖

如需更完整的文档转换能力，建议安装 `pandoc`。

## 启动方式

### 方式一：启动后端 API

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
```

也可以直接运行：

```bash
python server.py
```

默认服务地址：

- API: `http://localhost:8080`

### 方式二：启动前端

```bash
cd vue-web
npm run dev
```

默认前端地址：

- Web: `http://localhost:5173`

如需修改前端访问的后端地址，在 `vue-web` 下创建 `.env`：

```bash
VITE_API_BASE=http://localhost:8080
```

### 方式三：CLI 模式

```bash
python main_cli.py
```

适合快速验证 agent 基本运行链路，不适合替代完整 Web 交互。

## 前后端联调顺序

推荐顺序：

1. 配置数据库与 LLM
2. 启动 `server.py` / uvicorn
3. 启动 `vue-web`
4. 打开首页验证以下链路：
   - 普通输入发送
   - 上传附件发送
   - 示例流水线点击发送
   - 历史会话切换
   - 产物下载

## 工作区与附件机制

工作区默认根目录由 [config/app.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/app.yaml) 控制，通常为：

- `workspace/temp`
- `workspace/outputs`
- `workspace/artifacts`
- `workspace/logs`

当前附件相关链路分两类：

- 普通用户上传文件
  - 前端调用 `/workspace/upload`
  - 后端保存到 `/temp/<thread_id>/...`
  - 并记录到 `chat_files`
- 示例流水线预置文件
  - 前端创建消息后调用 `/message/attach`
  - 后端将示例文件路径登记为消息附件
  - 再通过 `/chat/stream` 作为本轮请求输入传给 agent

这意味着：

- 附件图标不仅是 UI 展示，还会写入数据库
- 刷新页面后，消息附件仍能通过 `/thread/messages` 回显

## 关键后端接口

当前前端直接依赖的主要接口如下：

- `POST /chat/stream`
  - 流式执行智能体
- `POST /chat`
  - 非流式执行
- `POST /threads/getTitles`
  - 获取会话列表
- `POST /thread/messages`
  - 获取某个会话的历史消息
- `POST /thread/delete`
  - 删除会话
- `POST /message/create`
  - 创建一条用户或助手消息
- `POST /message/attach`
  - 给某条消息登记附件
- `POST /workspace/upload`
  - 上传文件到工作区
- `GET /workspace/download`
  - 下载工作区文件
- `GET /skills/list`
  - 技能列表
- `GET /skills/types`
  - 技能类型统计

## 前端页面说明

当前 Web 端主要页面：

- 首页
  - 聊天输入
  - 文件上传
  - 3 个示例流水线
  - 历史会话
  - assistant 流式状态展示
- 技能中心
  - 展示技能列表与类型

示例流水线当前行为：

- 点击后新建会话 ID
- 自动创建用户消息
- 自动登记示例附件
- 自动发起流式任务执行

## 核心模块说明

### `runtime/engine.py`

项目主执行入口，负责：

- 初始化数据库
- 加载环境变量
- 初始化 MCP runtime
- 创建 agent
- 执行同步与流式对话

### `runtime/chat_store.py`

负责会话和消息持久化：

- `chat_threads`
- `messages`
- `chat_files`

### `runtime/workspace_manager.py`

负责工作区路径约束与虚拟路径解析，是附件上传和下载的基础设施。

### `agents/`

封装 DeepAgents 运行时的：

- prompt
- middleware
- 本地工具
- agent factory

### `mcp_runtime/`

负责 MCP server 生命周期管理，包括：

- client 初始化
- 健康检查
- 自动重连
- tool schema 注册