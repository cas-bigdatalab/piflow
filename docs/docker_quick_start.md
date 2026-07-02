# Docker 一键启动说明

本文档提供 `flow-deepagents-0408` 的 Docker 一键启动方案。

启动后包含：

- `postgres`：PostgreSQL 数据库
- `app`：一个容器内同时运行
  - FastAPI 后端
  - Nginx 托管的前端静态页面
  - Nginx 反代 API 到容器内后端

默认访问地址：

- 前端：`http://localhost:5174`
- 后端容器内部监听：`127.0.0.1:8081`

## 1. 前置条件

确保本机已安装：

- Docker
- Docker Compose Plugin

检查命令：

```bash
docker --version
docker compose version
```

## 2. 可选环境变量

如果你需要调用 LLM，请在启动前设置相关 API Key，例如：

```bash
export DASHSCOPE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export CSTCLOUD_API_KEY=your_key
export DEEPSEEK_API_KEY=your_key
export GLM_API_KEY=your_key
```

## 3. 一键启动

在仓库根目录执行：

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

首次启动会：

- 拉起 PostgreSQL
- 构建单一 `app` 镜像
- 在一个容器里同时启动后端与前端 Nginx

## 4. 查看状态

```bash
docker compose -f docker/docker-compose.yml ps
```

查看日志：

```bash
docker compose -f docker/docker-compose.yml logs -f app
docker compose -f docker/docker-compose.yml logs -f postgres
```

## 5. 停止服务

```bash
docker compose -f docker/docker-compose.yml down
```

如果连数据库卷一起清理：

```bash
docker compose -f docker/docker-compose.yml down -v
```

## 6. 目录说明

当前 Compose 方案会挂载这些目录：

- `../workspace:/app/workspace`
- `../storage:/app/storage`
- `../logs:/app/logs`

这样容器重启后，工作区和日志仍保留在宿主机。

数据库配置使用专门的 Docker 覆盖文件：

```text
docker/config/database.yaml
```

该文件默认连接 Compose 内的 `postgres` 服务。

## 7. 端口说明

- `5174:5174`：对外统一入口

如果端口冲突，可以在 `docker-compose.yml` 里修改宿主机左侧端口。

注意：这里指的是 [`docker/docker-compose.yml`](/Users/renhao/PycharmProjects/flow-deepagents-0408/docker/docker-compose.yml)。

## 8. 前端代理说明

`app` 容器内的 Nginx 已经内置以下能力：

- 托管 `vue-web` 打包产物
- 支持 React Router 的 `index.html` 回退
- 将 `/chat`、`/dag`、`/workspace`、`/message`、`/thread`、`/threads`、`/storage`、`/login`、`/user` 等 API 请求代理到同容器内的 `127.0.0.1:8081`

所以前端仍然保持：

```env
VITE_API_BASE=''
```

即可。

## 9. 常见问题

### 9.1 后端起不来

查看后端日志：

```bash
docker compose -f docker/docker-compose.yml logs -f app
```

重点检查：

- 数据库连接是否成功
- LLM 配置是否必填但缺失
- 某些 Python 依赖是否安装失败

### 9.2 前端能打开但接口报错

先确认：

```bash
docker compose -f docker/docker-compose.yml ps
```

然后检查前端和后端日志：

```bash
docker compose -f docker/docker-compose.yml logs -f app
```

### 9.3 数据库初始化失败

如果要彻底重置数据库：

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d --build
```

## 10. 推荐启动命令

日常推荐：

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

这就是当前项目的 Docker 一键启动方式。
