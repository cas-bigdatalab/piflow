# 化工模块集成维护说明

本文档记录 `chemical` 包当前如何接入 Flow DeepAgent 主应用。现在 `chemical` 已不再是完全独立的实验包，它已经通过启动流程、API 路由、PostgreSQL 和 PiFlow 远程执行服务与主产品产生耦合，后续维护时需要一起关注这些边界。

## 模块范围

`chemical` 模块目前提供以下能力：

- 读取化工计算节点配置。
- 将节点状态持久化到 PostgreSQL。
- 通过每个节点上的 PiFlow remote gRPC server 刷新资源信息。
- 在主 API 前缀下暴露化工节点查询与刷新接口。

代码仍放在顶层 `chemical/` 包中，但运行时已经依赖主产品基础设施。

## 主要耦合点

### 服务启动

文件：`server.py`

主 FastAPI 生命周期中导入：

```python
from chemical import chemical_router, get_chemical_service
```

在 `lifespan` 中，主产品的 `AgentEngine` 和 `PlannerEngine` 初始化完成后，会执行一次：

```python
get_chemical_service().refresh()
```

这次启动刷新被 `try/except` 包住。如果刷新失败，只记录日志，不阻断主服务启动。

维护注意：

- 如果以后希望化工刷新失败时阻断启动，需要调整 `server.py` 中的异常处理。
- 如果以后希望 `chemical` 再次变成独立部署模块，`server.py` 中的启动刷新和路由挂载是第一批要解除的耦合点。

### API 路由

文件：`server.py`

主 API router 中挂载了化工 router：

```python
api_router.include_router(chemical_router)
```

由于主 API 前缀是 `/api/piflow/v1`，所以实际接口路径为：

- `GET /api/piflow/v1/chemical/nodes`
- `GET /api/piflow/v1/chemical/nodes/{node_name}`
- `POST /api/piflow/v1/chemical/nodes/refresh`

文件：`chemical/node_api.py`

该文件负责化工 HTTP 接口，并维护一个 `ChemicalService` 单例。

配置文件解析顺序：

- 如果设置了环境变量 `CHEMICAL_CONFIG_PATH`，优先使用该路径。
- 否则如果存在 `chemical/config.yaml`，使用该文件。
- 否则回退到 `chemical/config.example.yaml`。

维护注意：

- 如果同一 HTTP 方法下同时存在静态路径和动态路径，路由顺序很重要。例如 `/nodes/refresh` 应放在 `/nodes/{node_name}` 之前，避免 `refresh` 被识别为节点名称。

### PostgreSQL

相关文件：

- `chemical/node_repository.py`
- `chemical/service.py`
- `database/postgres.py`
- `config/database.yaml`

`chemical` 包使用主产品的数据库连接：

```python
from database.postgres import get_connection
```

因此化工节点状态会写入 `config/database.yaml` 指向的同一个 PostgreSQL 实例。

当前表：

- `chemical_nodes`
- `chemical_node_software_instances`

`chemical_nodes` 保存节点身份、连接信息、配置软件列表、资源指标、状态、错误信息和刷新时间。

`chemical_node_software_instances` 保存每个 `(node_name, software)` 对应的软件运行实例数，即 `running_count`。

维护注意：

- 表结构由 `chemical/node_repository.py::ensure_schema` 创建。
- 当前没有单独的迁移文件；后续改表时应采用向后兼容写法，例如 `CREATE TABLE IF NOT EXISTS` 或 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`。

### PiFlow Remote Server

相关文件：

- `chemical/service.py`
- `piflow_engine/cn/piflow/remote/client.py`
- `piflow_engine/cn/piflow/remote/server.py`

化工资源刷新会调用每个配置节点上的 PiFlow remote server：

```python
RemoteExecutionClient(f"{node.ip}:{node.port}").get_server_resource()
```

远程服务返回以下资源字段：

- `cpu_cores`
- `memory_gb`
- `free_disk_gb`
- `hostname`

维护注意：

- 每个配置的化工节点都应启动一个 PiFlow remote gRPC server。
- 如果某个节点不可达，刷新会将该节点标记为 `unreachable`，并记录 `error_message`。
- 单个节点失败不应导致整个刷新失败。

## 刷新语义

启动刷新和手动刷新都调用 `ChemicalService.refresh()`。

刷新流程：

1. 检查 PostgreSQL 表是否存在，不存在则建表。
2. 读取化工配置文件。
3. 插入数据库中尚不存在的节点行。
4. 插入数据库中尚不存在的节点-软件实例行，初始 `running_count = 0`。
5. 调用每个节点的 PiFlow remote server，刷新资源字段。

重要约束：

- 已存在的节点名称不能被刷新改掉。
- 已存在的软件名称不能被刷新覆盖。
- 已存在的软件运行实例数量不能被刷新覆盖。

因此当前配置同步采用只插入、不覆盖的策略：

- `sync_config_nodes(...): ON CONFLICT (name) DO NOTHING`
- `ensure_software_instances(...): ON CONFLICT (node_name, software) DO NOTHING`

刷新只更新 `chemical_nodes` 中的资源和状态字段：

- `cpu_cores`
- `memory_gb`
- `free_disk_gb`
- `hostname`
- `status`
- `error_message`
- `last_refreshed_at`
- `updated_at`

## 查询语义

`GET /chemical/nodes` 不调用远程 gRPC server。

该接口只读取 PostgreSQL，并关联两张表：

- `chemical_nodes`
- `chemical_node_software_instances`

返回结果中包含节点资源信息，以及 `software_instances` 软件实例数字典。

示例返回结构：

```json
{
  "name": "chemical-node-1",
  "ip": "10.0.87.111",
  "port": 50061,
  "software": ["openbabel", "gaussian", "multiwfn"],
  "cpu_cores": 16.0,
  "memory_gb": 64.0,
  "free_disk_gb": 1024.0,
  "hostname": "node-host",
  "status": "healthy",
  "error_message": "",
  "last_refreshed_at": "2026-09-08T11:30:00+08:00",
  "software_instances": {
    "openbabel": 0,
    "gaussian": 1,
    "multiwfn": 0
  }
}
```

## 软件实例数

文件：`chemical/service.py`

对外方法：

- `has_software(node_name, software)`：判断节点是否具备某个软件。
- `set_software_instance_count(node_name, software, count)`：设置某个软件运行实例数。
- `change_software_instance_count(node_name, software, delta)`：按增量修改实例数，正数增加，负数减少。
- `increment_software_instance_count(node_name, software, delta=1)`：兼容旧命名，本质上调用增量修改。

文件：`chemical/node_repository.py`

`change_running_count` 使用 PostgreSQL 原子更新，并带非负约束：

```sql
UPDATE chemical_node_software_instances
SET running_count = running_count + %s
WHERE node_name = %s
  AND software = %s
  AND running_count + %s >= 0
RETURNING running_count
```

维护注意：

- 软件任务开始时调用 `change_software_instance_count(..., +1)`。
- 软件任务完成或失败时调用 `change_software_instance_count(..., -1)`。
- 资源刷新不能修改 `running_count`。

## 配置文件

文件：`chemical/config.py`

支持格式：

- `.yaml`
- `.yml`
- `.json`

配置结构：

```yaml
main_node:
  ip: 10.0.87.110
  port: 50061

nodes:
  - name: chemical-node-1
    ip: 10.0.87.111
    port: 50061
    software:
      - openbabel
      - gaussian
      - multiwfn
```

校验规则：

- `main_node` 必须是对象，只包含主节点连接所需的 `ip` 和 `port`。
- `main_node.ip` 必须是非空字符串。
- `main_node.port` 必须是 `1` 到 `65535` 之间的整数。
- `nodes` 必须是非空列表。
- `name` 和 `ip` 必须是非空字符串。
- `port` 必须是 `1` 到 `65535` 之间的整数。
- `software` 必须是非空字符串集合。
- 配置文件内节点名称必须唯一。

`main_node` 只保存在 `ChemicalConfig.main_node` 内存对象中，用于化工主服务的连接配置，不会写入 `chemical_nodes` 或 `chemical_node_software_instances` 表，也不会参与普通计算节点资源刷新。

维护注意：

- 因为刷新不会覆盖已有行，所以修改配置中的 `ip`、`port` 或 `software` 不会自动修改数据库中已有节点。
- 如果以后希望配置文件重新成为权威数据源，需要小心调整 `sync_config_nodes` 和 `ensure_software_instances`，并确保不覆盖 `running_count`。

## 当前文件职责

- `chemical/config.py`：配置模型与配置文件读取。
- `chemical/config.example.yaml`：示例节点配置。
- `chemical/node_api.py`：FastAPI 路由与 `ChemicalService` 单例。
- `chemical/node_repository.py`：PostgreSQL 表结构与 SQL 操作。
- `chemical/service.py`：业务编排、刷新、查询转换、软件实例数方法。
- `chemical/remote_pipeline_stop.py`：将一个化工节点或子 DAG 封装为远程执行 Stop。
- `chemical/dag_scheduler.py`：根据 skill 的 `required_software` 选择执行节点并生成化工调度 DAG。
- `chemical/__init__.py`：包级导出。
- `server.py`：主应用耦合入口，包含化工 router 挂载和启动刷新。

## DAG 调度

入口函数：

```python
from chemical import schedule_chemical_dag, schedule_chemical_dag_file

plan = schedule_chemical_dag(
    dag_definition,
    config=chemical_config,
)

plan = schedule_chemical_dag_file(
    "/path/to/workflow.json",
    config=chemical_config,
)
```

调度器只对内存中的待执行 DAG 做转换，不修改前端保存的原始 JSON 文件，也不改变主产品原有的 DAG 执行协议。

### skill 解析

每个 DAG 节点通过 `node.skill.skill_id` 定位 skill：

- 如果 `skill_id` 已经是 `skill.json` 的绝对路径，直接读取该文件。
- 如果 `skill_id` 是 skill UUID，调用 `runtime.dag_manager.get_dag_skill()` 获取 `skill_path`，再拼接工作区根目录和 `skill.json`。
- 也可以给 `schedule_chemical_dag(..., skill_json_resolver=...)` 注入解析器，适合测试或特殊部署环境。解析器可以返回 skill 字典，或者返回 `(skill 字典, skill.json 绝对路径)`。

skill.json 中的 `required_software` 支持字符串或字符串数组。数组表示同一个执行节点必须同时具备全部软件：

```json
{
  "required_software": ["gaussian", "multiwfn"]
}
```

### 节点选择和转换规则

1. 没有 `required_software` 的 skill 保留原节点，不转换。
2. 有 `required_software` 的 skill，先查找软件集合完整匹配的化工节点。
3. 主节点优先：启动过滤时会将 `nodes` 中所有与 `main_node.ip` 相同的节点的软件集合并入主节点；如果主节点具备所需软件，保持原节点在主服务本地执行，端口不要求相同。
4. 主节点不满足时，只从 IP 不同的配置节点中选择第一个匹配节点，并把原节点替换成 `ChemicalRemotePipelineStop`。
5. 没有任何节点满足软件要求时，调度直接抛出 `ValueError`，避免生成无法运行的 DAG。

远程包装节点包含以下三个参数：

- `node_definition_json`：原始节点定义；若能解析出 skill.json 路径，会把内部 `skill.skill_id` 规范化为该绝对路径。
- `target_server`：目标化工节点的 `ip:port`。
- `local_server`：配置中的 `main_node.ip:main_node.port`，用于远程节点回取本机输入文件。

远程 Stop 的动态输入端口只暴露原节点的 `reference` 输入；原节点的 `manual` 参数继续留在 `node_definition_json` 中。对于包含入口文件源节点的完整子 DAG，入口源节点参数会作为外部输入端口，用于替换成 `ChemicalFileSourceStop`。

### 调度维护边界

- 调度器不会把主节点写入 PostgreSQL，也不会修改节点资源或软件运行实例表。
- 调度器只负责选择执行位置和生成远程包装节点，不负责提交远程任务；真正提交由 `ChemicalRemotePipelineStop` 完成。
- 如果远程节点上的工作区路径与主节点不可见，输入会通过 `ChemicalFileSourceStop` 使用主节点的文件服务回取，必须确保远程 PiFlow server 能访问 `local_server`。
- 当前节点选择是配置顺序策略，不考虑实时负载；后续如需按 CPU、内存、磁盘或运行实例数调度，应在 `_select_execution_node` 中扩展，不要把负载逻辑散落到 Stop 中。
- `main_node` 的软件能力不是单独配置项，而是由 `nodes` 中所有同 IP 节点的软件集合自动归并得到。

## 运行检查清单

使用化工 API 前建议确认：

1. `config/database.yaml` 中配置的 PostgreSQL 可连接。
2. 每个化工节点都已启动 PiFlow remote server。
3. 已通过 `CHEMICAL_CONFIG_PATH` 指定真实配置文件，或已创建 `chemical/config.yaml`。
4. 主服务已启动。
5. 需要手动更新资源时，调用 `POST /api/piflow/v1/chemical/nodes/refresh`。
6. 查询当前数据库中的节点详情时，调用 `GET /api/piflow/v1/chemical/nodes`。

## 已知风险

- 启动刷新依赖 PostgreSQL 和远程 gRPC 可用性，不过当前失败只记录日志，不阻断主服务。
- 表结构创建逻辑写在 repository 代码中，尚未纳入正式迁移系统。
- 查询结果依赖至少执行过一次初始化或刷新。
- 刷新对节点身份和软件实例行采用只插入策略，因此过期的数据库行会被保留。
