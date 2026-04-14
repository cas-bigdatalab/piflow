# πFlowAgent Web (Vite + React + TypeScript)

## 开发启动

```bash
cd vue-web
npm install
npm run dev
```

默认后端地址为 `http://localhost:8080`（可通过环境变量覆盖）。

## 配置后端地址

在 `web/` 下创建 `.env`：

```bash
VITE_API_BASE=http://localhost:8080
```

## 已对接的后端接口

- `POST /chat/stream`：主页「开始加工」走 SSE 流式输出
- `POST /threads/getTitles`：左侧历史对话列表
- `POST /thread/delete`：删除对话
- `POST /thread/messages`：切换对话时加载消息
- `POST /workspace/upload`：主页上传附件
- `GET /workspace/download`：产物下载链接
- `GET /skills/list`：技能中心列表 + 关键字搜索

