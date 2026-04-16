# πFlow AI

[![中文说明](https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-red)](./README.zh-CN.md)

A research data processing prototype built on DeepAgents, FastAPI, skill integration, and a React frontend.

## Overview

- Streaming agent chat via `/chat/stream`
- Conversation history management: create, switch, delete, and load threads
- Workspace file handling: upload inputs and download outputs
- Message-level attachments: persisted for both uploaded files and preset example files
- Example pipelines: create a new thread and start a task in one click
- Skills center: list skills and categories

## Repository Structure

```text
flow-deepagents-0408/
├── server.py                  # FastAPI entrypoint
├── main_cli.py                # CLI entrypoint
├── requirements.txt           # Python dependencies
├── README.md
├── README.zh-CN.md
├── docs/
│   └── workspace_file_api.md  # Workspace file API notes
├── config/
│   ├── app.yaml
│   ├── database.yaml
│   ├── llm.yaml
│   └── mcp_servers.yaml
├── infra/                     # config, env, logging
├── runtime/                   # engine, chat store, workspace runtime
├── agents/                    # agent factory, prompts, middleware, tools
├── tools/                     # tool abstraction and adapters
├── mcp_runtime/               # MCP lifecycle and registration
├── workspace/                 # workspace root
├── storage/                   # static storage mount
├── test/                      # Python tests
└── vue-web/
    ├── package.json
    ├── README.md
    └── src/
        ├── components/
        ├── lib/
        └── pages/
```

## Prerequisites

### Python

Python 3.10+ is recommended.

Install backend dependencies:

```bash
pip install -r requirements.txt
```

### Node.js

Node.js 18+ is recommended for the frontend.

```bash
cd vue-web
npm install
```

### PostgreSQL

The project uses PostgreSQL for:

- chat threads
- messages
- message attachments
- skill metadata

Tables are created automatically on startup, but you must prepare the database first and configure [config/database.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/database.yaml).

Example:

```yaml
host: "127.0.0.1"
port: 5432
user: "postgres"
password: "123456"
name: "flow_agent"
```

### LLM configuration

Model provider settings come from config files and environment variables.

Check:

- [config/llm.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/llm.yaml)
- `.env` for provider API keys

Example:

```bash
DASHSCOPE_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### Optional dependency

Install `pandoc` if you need more complete document conversion support.

## Run the Project

### Start the backend API

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
```

Or:

```bash
python server.py
```

Default API base:

- `http://localhost:8080`

### Start the frontend

```bash
cd vue-web
npm run dev
```

Default frontend URL:

- `http://localhost:5173`

If you need a different backend base URL, create `vue-web/.env`:

```bash
VITE_API_BASE=http://localhost:8080
```

### Start CLI mode

```bash
python main_cli.py
```

This is useful for quick engine validation, but not a replacement for the web workflow.

## Recommended Local Flow

1. Configure PostgreSQL and the LLM provider
2. Start `server.py` / uvicorn
3. Start `vue-web`
4. Validate:
   - plain message sending
   - file upload and send
   - example pipeline trigger
   - thread switching
   - artifact download

## Workspace and Attachments

The workspace root is configured in [config/app.yaml](/Users/renhao/PycharmProjects/flow-deepagents-0408/config/app.yaml), typically with:

- `workspace/temp`
- `workspace/outputs`
- `workspace/artifacts`
- `workspace/logs`

There are currently two attachment paths:

- User-uploaded files
  - frontend calls `/workspace/upload`
  - backend stores them under `/temp/<thread_id>/...`
  - backend records them in `chat_files`
- Preset example files
  - frontend creates the message first
  - frontend calls `/message/attach`
  - backend records the file paths as message attachments
  - frontend includes those paths in `/chat/stream`

This means:

- attachment badges are not just UI-only
- attachments can still be restored after a page refresh through `/thread/messages`

## Key Backend APIs

The current frontend depends on:

- `POST /chat/stream`
- `POST /chat`
- `POST /threads/getTitles`
- `POST /thread/messages`
- `POST /thread/delete`
- `POST /message/create`
- `POST /message/attach`
- `POST /workspace/upload`
- `GET /workspace/download`
- `GET /skills/list`
- `GET /skills/types`

## Frontend Pages

Current pages include:

- Home
  - chat input
  - file upload
  - 3 example pipelines
  - thread history
  - assistant streaming state
- Skills
  - skill list and types

Current example pipeline behavior:

- creates a new thread
- creates a user message
- attaches preset example files
- starts a streaming task automatically

## Core Modules

### `runtime/engine.py`

Main runtime entry responsible for:

- database initialization
- env loading
- MCP runtime initialization
- agent creation
- sync and streaming execution

### `runtime/chat_store.py`

Persistence layer for:

- `chat_threads`
- `messages`
- `chat_files`

### `runtime/workspace_manager.py`

Handles workspace path validation and virtual path resolution.

### `agents/`

Contains:

- prompts
- middleware
- local tools
- agent factory

### `mcp_runtime/`

Handles MCP server lifecycle:

- client initialization
- health checks
- auto reconnect
- tool schema registration

## Testing and Troubleshooting

### Run tests

```bash
pytest
```

### Common checks

1. Backend fails to start
   - verify database config
   - verify LLM API key
   - verify MCP server config

2. Frontend cannot reach backend
   - verify `VITE_API_BASE`
   - verify backend is listening on `8080`

3. Attachment badge appears but download fails
   - verify the file exists in the workspace
   - verify the path registered through `/message/attach`

4. No SSE output
   - inspect `/chat/stream` in browser devtools
   - inspect backend logs for `chat stream request`

## Documentation Scope

This README reflects the current repository state and focuses on:

- how to run the project
- what the main modules do
- how the frontend and backend integrate today

For more detailed implementation references, see:

- [server.py](/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py)
- [vue-web/src/lib/api.ts](/Users/renhao/PycharmProjects/flow-deepagents-0408/vue-web/src/lib/api.ts)
- [docs/workspace_file_api.md](/Users/renhao/PycharmProjects/flow-deepagents-0408/docs/workspace_file_api.md)

`docs/workspace_file_api.md` still contains some historical content, so treat the code as the source of truth.
