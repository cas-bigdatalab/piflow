# Docker 离线部署说明

本文档用于在无法联网或不希望现场构建镜像的环境中部署 `piflow`。

## 1. 离线包内容

建议离线包至少包含这些文件：

```text
piflow/
├── images/
│   ├── piflow-2.0.0.tar
│   └── postgres-15.tar
├── docker/
│   ├── docker-compose.yml
│   └── config/
│       ├── database.yaml
│       └── llm.yaml
├── workspace/
├── storage/
└── logs/
```

说明：

- `piflow-2.0.0.tar`：应用镜像离线包，对应镜像 `registry.cn-hangzhou.aliyuncs.com/cnic-piflow/piflow:2.0.0`
- `postgres-15.tar`：PostgreSQL 官方镜像离线包
- `docker/docker-compose.yml`：Docker 启动配置
- `docker/config/database.yaml`：数据库配置，可在宿主机修改
- `docker/config/llm.yaml`：LLM 配置，可在宿主机修改
- `workspace`、`storage`、`logs`：宿主机挂载目录


## 2. 目标机器部署步骤

以下步骤从空目录开始。

### 2.1 创建部署目录

```bash
mkdir -p piflow
cd piflow
mkdir -p images docker/config workspace storage logs
```

### 2.2 拷贝离线文件

将以下文件复制到目标机器对应目录：

- `images/piflow-2.0.0.tar`
- `images/postgres-15.tar`
- `docker/docker-compose.yml`
- `docker/config/database.yaml`
- `docker/config/llm.yaml`

目录结构应与本文档第 1 节一致。

### 2.3 导入镜像

在 `piflow` 目录执行：

```bash
docker load -i images/piflow-2.0.0.tar
docker load -i images/postgres-15.tar
```

导入完成后可检查：

```bash
docker images | grep -E 'cnic-piflow/piflow|postgres'
```

### 2.4 修改配置文件

如有需要，可在宿主机直接修改：

- `docker/config/database.yaml`
- `docker/config/llm.yaml`

这两个文件都已挂载到容器内，修改后重启容器即可生效。

`docker/config/llm.yaml` 中各 provider 通过 `api_key_env` 读取宿主机环境变量。例如：

```yaml
llm:
  provider: dashscope
  model: qwen3.5-plus
  temperature: 0

providers:
  dashscope:
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: DASHSCOPE_API_KEY
```

这表示当 `provider: dashscope` 时，容器会读取宿主机传入的 `DASHSCOPE_API_KEY`。

需要在启动前配置 API Key，例如：

```bash
export DASHSCOPE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export CSTCLOUD_API_KEY=your_key
export DEEPSEEK_API_KEY=your_key
export GLM_API_KEY=your_key
```

常见对应关系如下：

- `dashscope` 对应 `DASHSCOPE_API_KEY`
- `cstcloud` 对应 `CSTCLOUD_API_KEY`
- `openai` 对应 `GLM_API_KEY`
- `deepseek` 对应 `DEEPSEEK_API_KEY`

### 2.5 启动服务

离线部署时不需要重新构建镜像，推荐使用：

```bash
docker compose -f docker/docker-compose.yml up -d --no-build
```

说明：

- `--no-build`：强制使用已导入的本地镜像
- `docker-compose.yml` 中已经声明了 `registry.cn-hangzhou.aliyuncs.com/cnic-piflow/piflow:2.0.0` 和 `postgres:15`

## 3. 验证部署

### 3.1 查看容器状态

```bash
docker ps -a --filter name=piflow
```

### 3.2 查看日志

```bash
docker logs -f piflow-app
docker logs -f piflow-postgres
```

### 3.3 访问前端

默认访问地址：

```text
http://127.0.0.1:5174/
```

### 3.4 调用接口验证

```bash
curl -X POST http://127.0.0.1:5174/threads/getTitles \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"default_user"}'
```

如果返回 JSON，而不是 `502 Bad Gateway`，说明后端接口已经正常。

## 4. 停止服务

```bash
docker compose -f docker/docker-compose.yml down
```

## 5. 重启后使配置生效

如果你修改了以下文件：

- `docker/config/database.yaml`
- `docker/config/llm.yaml`

可执行：

```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d --no-build
```

## 6. 常见说明

### 6.1 为什么离线部署不建议现场构建

因为 `registry.cn-hangzhou.aliyuncs.com/cnic-piflow/piflow:2.0.0` 镜像依赖较多，现场构建时可能遇到：

- 拉取基础镜像慢
- Python 依赖下载慢
- Node 依赖下载慢
- 网络限制导致构建失败

离线部署通过提前导出镜像，可以避免这些问题。

### 6.2 当前挂载目录

当前 Compose 会挂载这些宿主机目录：

- `./workspace -> /app/workspace`
- `./storage -> /app/storage`
- `./logs -> /app/logs`
- `./docker/config/database.yaml -> /app/config/database.yaml`
- `./docker/config/llm.yaml -> /app/config/llm.yaml`

### 6.3 PostgreSQL 镜像版本

当前内置数据库使用：

```text
postgres:15
```
