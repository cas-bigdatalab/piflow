# 调度系统设计方案

目标是把调度能力设计成一个独立的、数据库驱动的子系统，并继续复用当前项目已经具备的 DAG 执行引擎与 PiFlow 运行跟踪能力。

## 1. 背景

当前项目已有的 DAG 执行链路主要分为两部分：

- DAG 画板与定义管理
- PiFlow 执行引擎调用与运行状态跟踪

当前执行入口主要通过 `runtime/piflow_adapter.py` 中的 `submit_frontend_dag()` 完成。它负责：

- 将前端 DAG 转换为 PiFlow 可执行结构
- 启动 Runner 执行 DAG
- 将运行过程写入 `piflow_flow_run`、`piflow_stop_job_run` 等运行表

## 2. 设计目标

重设计后的调度系统应满足以下目标：

### 2.1 总体目标

- 参考 `piflow-java` 的调度设计思路
- 保持现有 PiFlow 执行引擎不变
- 保持前端 DAG 逻辑结构不变
- 调度状态、运行历史、恢复信息全部落库

### 2.2 行为目标

- 调度任务创建后可以持久化保存
- 服务重启后可以自动恢复已启动的调度任务
- 到点后由调度器主动触发 DAG 执行
- 每次触发都形成一条独立的调度运行记录
- 支持暂停、停止、删除、过期
- 支持错过触发时间后的补偿策略
- 支持限制同一调度任务的并发运行数
- 支持多实例下避免重复触发

### 2.3 架构边界

调度系统只负责：

- 记录“何时触发”
- 决定“是否触发”
- 到点后调用执行入口

调度系统不负责：

- 自己执行 DAG 节点
- 自己维护节点运行日志
- 替代 PiFlow 的运行跟踪表

也就是说，边界应保持为：

```text
逻辑 DAG / DAG 定义
    ->
调度子系统计算触发时机
    ->
submit_frontend_dag()
    ->
PiFlow 执行引擎
    ->
piflow_flow_run / piflow_stop_job_run
```

## 3. 总体架构

引入一个独立的 `runtime/schedule/` 包，形成如下架构：

```text
FastAPI API
    |
    v
ScheduleService
    |
    +-- ScheduleRepository
    +-- ScheduleExpression
    +-- ScheduleDispatcher
    +-- ScheduleLeaderLock
    |
    v
ScheduleDaemon
    |
    +-- 扫描到期任务
    +-- 抢占执行权
    +-- 创建 schedule_run
    +-- 调用 submit_frontend_dag()
    +-- 同步运行状态
```

该架构对应 `piflow-java` 中的几个核心思想：

- 调度任务定义持久化
- 服务启动时恢复已启动任务
- 独立后台线程进行周期性扫描
- 调度与执行解耦
- 停止与过期由独立逻辑处理

## 4. 目录与模块拆分

建议新增如下目录结构：

```text
runtime/
└── schedule/
    ├── __init__.py
    ├── constants.py
    ├── models.py
    ├── errors.py
    ├── repository.py
    ├── expression.py
    ├── lock.py
    ├── dispatcher.py
    ├── daemon.py
    └── service.py

schemas/
└── schedule/
    ├── __init__.py
    └── schedule_schema.py

routers/
└── schedule_router.py

test/
├── test_schedule_expression.py
├── test_schedule_repository.py
├── test_schedule_daemon.py
└── test_schedule_api.py
```

下面分别说明每个模块的职责。

### 4.1 `runtime/schedule/constants.py`

统一定义调度系统中的状态和枚举值，避免字符串散落在代码各处。

建议包含：

- 调度任务状态
- 调度运行状态
- 触发器类型
- 错过执行策略
- 并发策略

示例：

```python
class ScheduleStatus:
    DRAFT = "DRAFT"
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"


class ScheduleRunStatus:
    PENDING = "PENDING"
    DISPATCHING = "DISPATCHING"
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    LOST = "LOST"


class TriggerType:
    ONCE = "ONCE"
    CRON = "CRON"
    INTERVAL = "INTERVAL"


class MisfirePolicy:
    SKIP = "SKIP"
    FIRE_ONCE = "FIRE_ONCE"
    CATCH_UP = "CATCH_UP"
```

### 4.2 `runtime/schedule/models.py`

定义内部领域模型，封装调度任务与调度运行对象。

建议不要直接把数据库行在系统内部到处传递，而是统一映射成 Python 模型对象，例如：

- `ScheduleJob`
- `ScheduleRun`
- `LeaderLease`

示例字段：

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ScheduleJob:
    schedule_job_id: str
    dag_task_id: str
    definition_id: str
    owner_id: str
    name: str
    trigger_type: str
    cron_expression: str | None
    interval_seconds: int | None
    start_time: datetime | None
    end_time: datetime | None
    timezone: str
    misfire_policy: str
    max_running_instances: int
    status: str
    next_fire_time: datetime | None
    last_fire_time: datetime | None
    payload: dict[str, Any]


@dataclass
class ScheduleRun:
    schedule_run_id: str
    schedule_job_id: str
    planned_fire_time: datetime
    actual_fire_time: datetime | None
    process_id: str | None
    status: str
    attempt: int
    error_message: str | None
```

### 4.3 `runtime/schedule/errors.py`

定义调度系统的专用异常，例如：

- `ScheduleNotFoundError`
- `InvalidScheduleExpressionError`
- `ScheduleOwnershipError`
- `ScheduleConcurrencyExceededError`
- `ScheduleDispatchLostError`

这样 service 层与 router 层可以更清晰地做错误映射。

### 4.4 `runtime/schedule/repository.py`

该模块只负责数据库访问，不负责 cron 计算，也不调用执行引擎。

职责包括：

- 创建调度任务
- 查询调度任务
- 查询调度运行历史
- 修改任务状态
- 抢占到期任务
- 创建调度运行记录
- 标记调度运行为 `DISPATCHING`
- 提交成功后写回 `process_id`
- 恢复异常租约
- 查询正在运行中的调度实例数量

建议提供的方法包括：

- `create_job(...)`
- `get_job(schedule_job_id, owner_id)`
- `list_jobs(owner_id, ...)`
- `update_job(...)`
- `start_job(...)`
- `pause_job(...)`
- `stop_job(...)`
- `delete_job(...)`
- `claim_due_jobs(...)`
- `create_run_if_absent(...)`
- `mark_run_dispatching(...)`
- `mark_run_submitted(...)`
- `mark_run_failed(...)`
- `advance_next_fire_time(...)`
- `count_active_runs(schedule_job_id)`
- `recover_expired_dispatching_runs(...)`

### 4.5 `runtime/schedule/expression.py`

该模块负责处理触发时间的全部逻辑。

主要职责：

- 验证 cron 表达式
- 验证 `start_time/end_time/timezone`
- 计算 `next_fire_time`
- 支持一次性任务、cron 任务、间隔任务
- 支持错过触发时间后的补偿计算

建议仅在本模块内部引入表达式计算库，例如 `croniter`。这样即使将来替换实现，也不会影响调度系统其他模块。

推荐接口形式：

```python
class ScheduleExpression:
    def __init__(self, *, trigger_type: str, cron_expression: str | None, interval_seconds: int | None, timezone: str):
        ...

    def validate(self) -> None:
        ...

    def first_fire_time(self, start_time: datetime | None, now: datetime) -> datetime | None:
        ...

    def next_fire_time(self, after: datetime) -> datetime | None:
        ...
```

### 4.6 `runtime/schedule/lock.py`

用于多实例调度场景下防止重复触发。

主要职责：

- 获取全局 leader lease
- 续约 lease
- 释放 lease
- 判断当前实例是否仍是 leader

如果当前系统未来只部署单实例，这个模块也建议保留，因为：

- 实现成本不高
- 后续扩展多实例时不需要重新设计
- Uvicorn reload、多 worker、本地多进程调试都可能造成重复调度

### 4.7 `runtime/schedule/dispatcher.py`

调度系统中真正连接执行引擎的唯一模块。

职责只有一个：

- 当某个调度运行被确认应该触发时，读取对应的 DAG 版本定义，并调用 `submit_frontend_dag()`

推荐不要把 DAG 提交逻辑散落到 daemon 或 service 层，而是集中到 dispatcher。

建议 dispatcher 做的事情：

- 根据 `definition_id` 读取对应 DAG 定义
- 读取调度 payload 中的执行参数
- 调用 `submit_frontend_dag()`
- 获取返回的 `process_id`
- 将提交结果返回给 daemon

### 4.8 `runtime/schedule/daemon.py`

这是调度子系统的核心常驻后台组件，负责：

- 启动时恢复调度
- 周期性扫描到期任务
- 抢占调度触发权
- 创建调度运行记录
- 调用 dispatcher 发起执行
- 低频同步调度运行状态
- 处理到期任务与异常租约

daemon 应是一个后台线程或协程管理器，不应依赖 FastAPI request 生命周期。

### 4.9 `runtime/schedule/service.py`

该层面向 API 与业务调用，是调度系统的业务编排层。

职责包括：

- 创建调度任务
- 更新调度任务
- 启动、暂停、停止、删除
- 查询调度列表和详情
- 查询调度执行历史
- 校验 DAG 归属关系
- 决定是否绑定当前定义版本

该层不应包含大量 SQL，也不应直接自己计算 cron 逻辑。

## 5. 数据库表设计

当前项目已经有：

- `dag_task`
- `dag_definition`
- `piflow_flow_run`
- `piflow_stop_job_run`

因此新的调度表应尽量只补充“调度语义”，不要重复定义 DAG 和运行引擎已有的结构。

建议新增三张表：

- `schedule_job`
- `schedule_run`
- `schedule_leader_lock`

### 5.1 `schedule_job`

该表表示一个长期存在的调度任务定义。

建议表结构如下：

```sql
CREATE TABLE IF NOT EXISTS schedule_job (
    id BIGSERIAL PRIMARY KEY,

    schedule_job_id VARCHAR(128) NOT NULL,
    schedule_name VARCHAR(255) NOT NULL,

    dag_task_id VARCHAR(128) NOT NULL,
    definition_id VARCHAR(128) NOT NULL,
    owner_id VARCHAR(128) NOT NULL,

    trigger_type VARCHAR(32) NOT NULL,
    cron_expression VARCHAR(255),
    interval_seconds INTEGER,

    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai',

    misfire_policy VARCHAR(32) NOT NULL DEFAULT 'FIRE_ONCE',
    max_running_instances INTEGER NOT NULL DEFAULT 1,
    concurrency_policy VARCHAR(32) NOT NULL DEFAULT 'SKIP_CURRENT',

    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',

    next_fire_time TIMESTAMPTZ,
    last_fire_time TIMESTAMPTZ,

    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_schedule_job_id UNIQUE (schedule_job_id),

    CONSTRAINT ck_schedule_trigger_type CHECK (
        trigger_type IN ('ONCE', 'CRON', 'INTERVAL')
    ),

    CONSTRAINT ck_schedule_status CHECK (
        status IN ('DRAFT', 'STARTED', 'PAUSED', 'STOPPED', 'EXPIRED', 'DELETED')
    )
);

CREATE INDEX IF NOT EXISTS idx_schedule_job_due
    ON schedule_job(status, next_fire_time);

CREATE INDEX IF NOT EXISTS idx_schedule_job_owner
    ON schedule_job(owner_id, status);

CREATE INDEX IF NOT EXISTS idx_schedule_job_task
    ON schedule_job(dag_task_id, status);
```

主要字段解释：

- `schedule_job_id`：业务主键
- `schedule_name`：前端展示名称
- `dag_task_id`：关联 DAG 任务
- `definition_id`：绑定的 DAG 定义版本
- `owner_id`：所属用户
- `trigger_type`：触发器类型
- `cron_expression`：cron 表达式
- `interval_seconds`：间隔任务秒数
- `start_time/end_time`：有效时间区间
- `timezone`：时区
- `misfire_policy`：错过触发后的补偿策略
- `max_running_instances`：最多允许几个同时运行
- `concurrency_policy`：超过并发限制时如何处理
- `next_fire_time`：下一次触发时间
- `last_fire_time`：最近一次成功推进的计划时间
- `payload_json`：扩展执行参数

### 5.2 `schedule_run`

该表表示某个调度任务的一次实际触发记录。

建议表结构如下：

```sql
CREATE TABLE IF NOT EXISTS schedule_run (
    id BIGSERIAL PRIMARY KEY,

    schedule_run_id VARCHAR(128) NOT NULL,
    schedule_job_id VARCHAR(128) NOT NULL,

    dag_task_id VARCHAR(128) NOT NULL,
    definition_id VARCHAR(128) NOT NULL,
    owner_id VARCHAR(128) NOT NULL,

    planned_fire_time TIMESTAMPTZ NOT NULL,
    actual_fire_time TIMESTAMPTZ,

    process_id VARCHAR(128),

    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    attempt INTEGER NOT NULL DEFAULT 0,

    dispatch_owner VARCHAR(128),
    dispatch_lease_until TIMESTAMPTZ,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_schedule_run_id UNIQUE (schedule_run_id),

    CONSTRAINT uk_schedule_run_job_planned_fire UNIQUE (
        schedule_job_id, planned_fire_time
    ),

    CONSTRAINT ck_schedule_run_status CHECK (
        status IN (
            'PENDING',
            'DISPATCHING',
            'SUBMITTED',
            'RUNNING',
            'SUCCESS',
            'FAILED',
            'CANCELLED',
            'LOST'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_schedule_run_job
    ON schedule_run(schedule_job_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_schedule_run_status
    ON schedule_run(status, updated_at);

CREATE INDEX IF NOT EXISTS idx_schedule_run_process
    ON schedule_run(process_id);
```

其中 `UNIQUE (schedule_job_id, planned_fire_time)` 非常关键，它能保证：

- 同一时间点的同一次调度只生成一条运行记录
- 多实例扫描不会重复插入
- 恢复补偿不会重复创建相同执行记录

### 5.3 `schedule_leader_lock`

该表用于多实例调度下的 leader 选举或租约机制。

建议结构如下：

```sql
CREATE TABLE IF NOT EXISTS schedule_leader_lock (
    lock_name VARCHAR(128) PRIMARY KEY,
    owner_id VARCHAR(128),
    lease_until TIMESTAMPTZ,
    heartbeat_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

初始化时可插入一条固定记录：

```sql
INSERT INTO schedule_leader_lock(lock_name)
VALUES ('global-scheduler')
ON CONFLICT (lock_name) DO NOTHING;
```

## 6. 为什么调度任务必须绑定 `definition_id`

调度任务不应该只保存 `dag_task_id`，还应保存当时对应的 `definition_id`。

原因如下：

假设用户今天创建了一个调度任务，绑定的是 DAG 版本 A。之后用户又修改画板，产生了版本 B。

如果调度系统每次触发时都只按 `dag_task_id` 读取“当前最新版本”，那么历史调度任务会在没有显式变更的情况下自动执行新版本 DAG，这会带来以下问题：

- 行为不可追溯
- 历史调度结果难以解释
- 用户对“同一个调度为什么今天行为变了”没有感知

因此建议默认使用固定版本绑定：

- `dag_task_id`：指向任务
- `definition_id`：指向具体版本

后续如果需要“总是执行最新版本”的模式，可以额外增加：

- `definition_mode = FIXED / LATEST`

但默认仍应使用 `FIXED`。

## 7. 状态机设计

### 7.1 调度任务状态机

建议状态流转如下：

```text
DRAFT
  |
  v
STARTED <----> PAUSED
  |
  v
STOPPED

STARTED --到达 end_time--> EXPIRED

任意可见状态 --逻辑删除--> DELETED
```

状态说明：

- `DRAFT`：已保存但尚未启动
- `STARTED`：调度器会扫描并触发
- `PAUSED`：保留配置但暂不触发
- `STOPPED`：显式停止，不再触发
- `EXPIRED`：超过 `end_time`
- `DELETED`：逻辑删除

### 7.2 调度运行状态机

建议状态流转如下：

```text
PENDING
  |
  v
DISPATCHING
  |
  v
SUBMITTED
  |
  v
RUNNING
  +--> SUCCESS
  +--> FAILED
  +--> CANCELLED

DISPATCHING --租约过期/状态不明--> LOST
SUBMITTED   --无法确认提交结果--> LOST
```

状态说明：

- `PENDING`：已确定需要执行，但尚未进入提交阶段
- `DISPATCHING`：某个实例已抢占并开始提交 DAG
- `SUBMITTED`：已调用执行引擎成功拿到 `process_id`
- `RUNNING`：已在 PiFlow 运行中
- `SUCCESS`：运行成功
- `FAILED`：运行失败
- `CANCELLED`：运行被主动停止
- `LOST`：提交过程中发生不确定异常，无法断定是否已成功执行

## 8. 调度计算与触发规则

### 8.1 触发类型

建议第一阶段支持三类触发器：

- `ONCE`
- `CRON`
- `INTERVAL`

#### `ONCE`

一次性任务，只触发一次。触发完成后：

- `next_fire_time = NULL`
- `status` 可以自动转 `STOPPED` 或 `EXPIRED`

#### `CRON`

基于 cron 表达式计算下一次执行时间。

如果要对齐 `piflow-local` 的风格，建议明确使用带秒位的 Quartz 风格表达式，例如：

```text
0 */5 * * * *
```

表示每 5 分钟触发一次。

#### `INTERVAL`

按照固定秒数间隔执行，例如：

- 每 60 秒
- 每 300 秒
- 每 3600 秒

### 8.2 `next_fire_time` 的设计原则

`next_fire_time` 必须持久化到数据库，而不是每次服务重启后临时重新计算。这样做的好处是：

- 行为可追踪
- 补偿逻辑更明确
- 避免时区与基准时间变化造成不一致
- 更方便多实例共享调度状态

### 8.3 错过执行时间后的策略

服务停机或调度线程阻塞时，可能错过多个触发点。建议支持三种策略：

- `SKIP`
- `FIRE_ONCE`
- `CATCH_UP`

#### `SKIP`

跳过所有错过的执行点，直接推进到下一个未来时间。

适合：

- 不关心补跑
- 任务高频且幂等性差

#### `FIRE_ONCE`

不管错过多少次，恢复后只补一次，然后再推进下一个执行点。

适合：

- 大多数业务场景
- 既不想完全丢失触发，也不想短时间补跑大量任务

#### `CATCH_UP`

错过几个时间点，就补跑几次。

适合：

- 对每个计划时间点都有强要求的场景

但该策略应额外配合最大补偿上限，例如：

- `max_catch_up_runs = 100`

避免长时间停机后瞬间创建过多运行记录。

## 9. 调度循环设计

建议使用独立后台线程实现，而不是再引入通用调度框架。

示意结构如下：

```python
class ScheduleDaemon:
    def __init__(self, repository, dispatcher, leader_lock, poll_interval: float = 1.0):
        self.repository = repository
        self.dispatcher = dispatcher
        self.leader_lock = leader_lock
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread = None
```

### 9.1 启动流程

建议启动时执行以下动作：

1. 初始化调度相关数据库表
2. 恢复异常中的 `DISPATCHING` 运行记录
3. 获取或竞争 leader lease
4. 启动后台扫描线程

### 9.2 主循环

主循环建议如下：

```python
def _run(self):
    while not self._stop_event.is_set():
        try:
            if self.leader_lock.try_acquire_or_renew():
                self._tick()
        except Exception:
            log.exception("schedule daemon tick failed")

        self._stop_event.wait(self.poll_interval)
```

### 9.3 每个 tick 的主要工作

每个扫描周期建议执行：

1. 自动过期 `end_time` 已到的任务
2. 恢复租约超时的 `DISPATCHING` 运行
3. 扫描当前到期任务
4. 为每个到期任务创建运行记录
5. 根据并发策略判断是否允许执行
6. 调用 dispatcher 发起 DAG 提交
7. 推进 `next_fire_time`
8. 低频同步 `SUBMITTED/RUNNING` 状态

## 10. 到期任务如何抢占

多实例或多线程下，不能使用“先查出所有到期任务，再逐条更新”的方式，否则多个实例会同时看到同一批任务。

正确做法是使用数据库行锁和原子事务。

建议 SQL 形式：

```sql
SELECT *
FROM schedule_job
WHERE status = 'STARTED'
  AND next_fire_time IS NOT NULL
  AND next_fire_time <= NOW()
ORDER BY next_fire_time
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

选出后，在同一事务中：

- 计算本次计划触发时间
- 创建 `schedule_run`
- 推进 `last_fire_time`
- 计算新的 `next_fire_time`

这一步完成后即使后面的提交逻辑失败，也不会被别的实例重复拿到同一条记录。

## 11. 单次触发的完整执行流程

建议把一次调度触发拆成三个阶段。

### 11.1 阶段一：创建调度运行记录

首先根据 `schedule_job_id + planned_fire_time` 创建唯一的一条运行记录。

推荐使用：

```sql
INSERT INTO schedule_run (
    schedule_run_id,
    schedule_job_id,
    dag_task_id,
    definition_id,
    owner_id,
    planned_fire_time,
    status
)
VALUES (...)
ON CONFLICT (schedule_job_id, planned_fire_time) DO NOTHING;
```

如果没有插入成功，说明这次触发已经被别的实例处理过，当前实例应直接跳过。

### 11.2 阶段二：进入 `DISPATCHING`

在真正调用执行引擎前，应先将 `schedule_run` 标记为：

- `status = DISPATCHING`
- `dispatch_owner = 当前实例ID`
- `dispatch_lease_until = 当前时间 + 租约时长`
- `attempt = attempt + 1`

这样可以表示：

- 这条记录正在由某个实例提交
- 若该实例崩溃，其他实例可在租约超时后进行恢复处理

### 11.3 阶段三：调用执行引擎

dispatching 成功后，由 `dispatcher.py` 负责：

1. 按 `definition_id` 读取固定版本 DAG 定义
2. 读取必要的执行上下文
3. 调用 `submit_frontend_dag()`
4. 取回 `process_id`

示意代码：

```python
process = submit_frontend_dag(
    definition_json=definition_json,
    workspace_root=workspace_root,
    user_id=job.owner_id,
    python_home=python_home,
)
process_id = process.pid()
```

随后更新 `schedule_run`：

- `status = SUBMITTED`
- `actual_fire_time = now`
- `process_id = process_id`
- 清理 dispatch lease 字段

## 12. 与现有 PiFlow 运行跟踪如何协同

当前项目中，PiFlow 的真实运行状态已经由：

- [`runtime/piflow_adapter.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/piflow_adapter.py)
- [`runtime/piflow_run_query.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/piflow_run_query.py)

配合以下表完成：

- `piflow_flow_run`
- `piflow_stop_job_run`

因此新的调度系统不应重复实现整套运行状态存储，而是采用“关联而不替代”的方式。

建议关系如下：

- `schedule_job`：定义调度配置
- `schedule_run`：记录每次触发
- `schedule_run.process_id`：关联 `piflow_flow_run.process_id`

### 12.1 运行状态同步方式

可以有两种方式：

#### 方式一：查询时联表或二次查询

API 查询 `schedule_run` 时，附带去查对应的 `piflow_flow_run`，再组合返回。

优点：

- 不重复存储真实运行状态
- 逻辑更简单

#### 方式二：后台周期性同步

daemon 每隔几秒扫描：

- `SUBMITTED`
- `RUNNING`

再通过 `get_piflow_run_progress(process_id)` 查询 PiFlow 状态，并回写 `schedule_run.status`。

建议状态映射：

- PiFlow `RUNNING` -> `RUNNING`
- PiFlow `SUCCEED` -> `SUCCESS`
- PiFlow `FAILED` -> `FAILED`
- PiFlow `ABORTED` -> `CANCELLED`

第一阶段更推荐方式一，因为实现更简单。

## 13. 并发控制设计

同一个调度任务的下一次触发时间到来时，前一次 DAG 可能仍在运行。

因此应增加：

- `max_running_instances`
- `concurrency_policy`

### 13.1 `max_running_instances`

表示同一个 `schedule_job` 最多允许几个活跃运行：

- `1`：最常见，也是建议默认值
- `2` 或更高：适合明确可并发的场景

活跃运行通常指：

- `DISPATCHING`
- `SUBMITTED`
- `RUNNING`

### 13.2 `concurrency_policy`

当活跃运行数已经达到上限时，可以考虑三种策略：

- `SKIP_CURRENT`
- `QUEUE_CURRENT`
- `FAIL_CURRENT`

推荐默认值：

- `max_running_instances = 1`
- `concurrency_policy = SKIP_CURRENT`

这样可以避免长时间运行的 DAG 导致任务大量积压。

## 14. 多实例防重设计

如果服务以以下方式运行：

- Uvicorn 多 worker
- 多容器副本
- reload 模式
- 本地多实例启动

就不能依赖 Python 全局变量、线程锁或单进程内存来避免重复调度。

建议使用数据库租约机制。

### 14.1 leader lease 方案

通过更新 `schedule_leader_lock` 表来争抢全局调度领导权：

```sql
UPDATE schedule_leader_lock
SET
    owner_id = %(owner_id)s,
    lease_until = CURRENT_TIMESTAMP + INTERVAL '15 seconds',
    heartbeat_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE lock_name = 'global-scheduler'
  AND (
      lease_until IS NULL
      OR lease_until < CURRENT_TIMESTAMP
      OR owner_id = %(owner_id)s
  )
RETURNING owner_id;
```

行为建议如下：

- 每 5 秒续约一次
- 租约时长 15 秒
- 若续约失败，当前实例停止触发新的调度任务
- 已经提交出去的 DAG 不受影响

## 15. 服务重启恢复设计

服务重启后，调度系统应能够恢复运行，而不是丢失所有调度状态。

建议恢复逻辑包括以下几部分。

### 15.1 恢复已启动任务

daemon 启动后自动扫描：

- `status = STARTED`

的 `schedule_job`，并直接进入统一扫描流程。这里不需要像 APScheduler 那样把每条 job 重新注册进一个外部调度器，只需要数据库中有记录即可。

### 15.2 恢复异常中的 `DISPATCHING`

若服务在以下时刻崩溃：

- 已把 `schedule_run` 标记为 `DISPATCHING`
- 但还没来得及写回 `process_id`

则恢复时需要检查：

- `dispatch_lease_until` 是否已过期

若过期，可将其标记为：

- `LOST`

或者视策略改回 `PENDING`，等待重新分发。

建议第一版更保守，先标记为 `LOST`，避免重复执行。

### 15.3 恢复错过的触发

恢复时若发现 `next_fire_time <= now`，则按该任务的 `misfire_policy` 处理：

- `SKIP`
- `FIRE_ONCE`
- `CATCH_UP`

## 16. FastAPI 接入方式

当前项目的 [`server.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py) 已使用 `lifespan` 管理启动和关闭流程，因此调度 daemon 最适合在这里接入。

建议接入流程如下：

1. 初始化日志
2. 初始化基础数据库表
3. 初始化 PiFlow 运行跟踪表
4. 初始化 AgentEngine / PlannerEngine
5. 构建并启动 `ScheduleDaemon`
6. 应用关闭时先停止 daemon，再关闭其他引擎

示意代码：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logging()

    initialize_datasource_catalog_schema()

    engine = AgentEngine()
    planner_engine = PlannerEngine()

    await engine.initialize()
    await planner_engine.initialize()

    schedule_daemon = build_schedule_daemon()
    schedule_daemon.start()

    app.state.engine = engine
    app.state.planner_engine = planner_engine
    app.state.schedule_daemon = schedule_daemon

    try:
        yield
    finally:
        schedule_daemon.stop()
        await planner_engine.shutdown()
        await engine.shutdown()
```

注意事项：

- 不要在模块导入时自动启动调度线程
- 不要把 daemon 放到全局变量初始化里
- 统一通过 `lifespan` 控制启动和停止

## 17. API 设计建议

建议新增独立的调度路由，而不是把调度操作塞进现有 DAG 运行 API 中。

建议接口如下：

- `POST /api/piflow/v1/schedules`
- `GET /api/piflow/v1/schedules`
- `GET /api/piflow/v1/schedules/{schedule_job_id}`
- `PUT /api/piflow/v1/schedules/{schedule_job_id}`
- `POST /api/piflow/v1/schedules/{schedule_job_id}/start`
- `POST /api/piflow/v1/schedules/{schedule_job_id}/pause`
- `POST /api/piflow/v1/schedules/{schedule_job_id}/stop`
- `DELETE /api/piflow/v1/schedules/{schedule_job_id}`
- `GET /api/piflow/v1/schedules/{schedule_job_id}/runs`
- `GET /api/piflow/v1/schedule-runs/{schedule_run_id}`
- `POST /api/piflow/v1/schedule-runs/{schedule_run_id}/cancel`

### 17.1 创建调度请求示例

```json
{
  "schedule_name": "每日语料处理",
  "dag_task_id": "dag-001",
  "definition_id": "definition-001",
  "trigger_type": "CRON",
  "cron_expression": "0 0 10 * * ?",
  "timezone": "Asia/Shanghai",
  "start_time": "2026-09-03T10:00:00+08:00",
  "end_time": null,
  "misfire_policy": "FIRE_ONCE",
  "max_running_instances": 1,
  "concurrency_policy": "SKIP_CURRENT"
}
```

### 17.2 API 输入建议

建议前端创建调度任务时只传：

- `dag_task_id`
- `definition_id`
- 调度策略字段

不建议直接把完整 DAG JSON 作为调度任务内容传入，因为 DAG 本身已经在 `dag_definition` 中持久化了。

## 18. 权限与校验设计

调度任务必须严格按用户归属进行隔离。

### 18.1 创建前校验

创建调度任务时，至少校验：

1. `dag_task_id` 存在
2. DAG 归属当前用户
3. `definition_id` 属于该 DAG
4. `definition_id` 对应记录归属当前用户
5. `trigger_type` 与配置字段匹配
6. cron 表达式合法
7. `start_time < end_time`
8. 时区合法

### 18.2 查询与修改校验

所有读取、修改、删除接口都应按如下条件查找：

```sql
WHERE schedule_job_id = %s
  AND owner_id = %s
  AND status <> 'DELETED'
```

不要仅按 `schedule_job_id` 查询后再在 Python 层补判断，否则容易留下越权漏洞。

## 19. 推荐实现顺序

建议按最小可行版本逐步推进，而不是一次性完成所有功能。

### 19.1 第一阶段：可运行最小版本

建议先实现：

- `schedule_job`
- `schedule_run`
- `schedule_leader_lock`
- `CRON` 触发
- `STARTED / PAUSED / STOPPED`
- `FIRE_ONCE`
- `max_running_instances = 1`
- 单实例 daemon
- 调度 CRUD API

### 19.2 第二阶段：增强能力

后续再补充：

- `ONCE`
- `INTERVAL`
- `CATCH_UP`
- 更丰富的状态同步
- 多实例抢占验证
- 调度运行取消
- 失败重试策略

### 19.3 建议实施步骤

1. 新增调度相关表结构
2. 在 `runtime/schedule/` 下建立包结构
3. 实现 `constants.py`、`models.py`
4. 实现 `expression.py`
5. 实现 `repository.py`
6. 为 repository 和 expression 写测试
7. 实现 `dispatcher.py`
8. 实现 `daemon.py`
9. 接入 `server.py` 的 `lifespan`
10. 实现 `service.py`
11. 新增 `schedule_router.py`
12. 增加 API 测试
13. 做重启恢复测试
14. 做并发与防重测试
15. 删除 `runtime/scheduler_manager.py`
16. 从 `requirements.txt` 删除 `apscheduler`

## 20. 与现有代码的迁移关系

### 20.1 保留不动的部分

建议继续复用：

- [`runtime/piflow_adapter.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/piflow_adapter.py)
- [`runtime/piflow_run_query.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/piflow_run_query.py)
- [`runtime/dag_manager.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/dag_manager.py)
- [`services/dag_panel_service.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/services/dag_panel_service.py)

原因是这些模块已经分别承担了：

- DAG 提交执行
- PiFlow 运行状态查询
- DAG 数据库初始化
- DAG 定义保存与读取

新调度系统应建立在这些稳定能力之上。

### 20.2 最终可删除的部分

在新调度系统完全落地后，可删除：

- [`runtime/scheduler_manager.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/runtime/scheduler_manager.py)

同时可从 [`requirements.txt`](/Users/renhao/PycharmProjects/flow-deepagents-0408/requirements.txt) 删除：

- `apscheduler`

若需要 cron 表达式计算库，可新增：

- `croniter`

但应限制在 `runtime/schedule/expression.py` 内部使用。

## 21. 风险与注意事项

### 21.1 不要把调度和执行混在一起

调度层应只负责“何时执行”和“是否执行”，不应自己承担 DAG 节点执行语义。

### 21.2 不要默认执行最新 DAG

应默认绑定 `definition_id`，否则用户修改画板后历史调度任务行为会无提示变化。

### 21.3 不要乐观假设提交一定成功

调用 `submit_frontend_dag()` 并不是数据库事务的一部分，因此一定要显式设计：

- `DISPATCHING`
- `LOST`
- 重试或人工恢复路径

### 21.4 不要只靠内存锁

只用 Python 线程锁不足以解决：

- 多进程
- 多实例
- reload

因此必须使用数据库租约或数据库锁。

### 21.5 先做最小闭环

第一版不建议同时追求：

- 所有触发器
- 所有补偿策略
- 自动重试
- 复杂依赖编排

建议先把下面这条链路打通：

```text
创建调度任务
    ->
任务入库
    ->
daemon 扫描到期
    ->
生成 schedule_run
    ->
调用 submit_frontend_dag()
    ->
拿到 process_id
    ->
API 可查询执行历史
```

## 22. 结论

这套方案的核心，不是用另一个 Python 调度框架替换 `APScheduler`，而是将调度能力收回到项目自己的运行时体系中。

其本质设计思想与 `piflow-local` 一致：

- 调度任务落库
- 服务启动可恢复
- 独立后台循环扫描
- 到点后只负责触发执行
- 执行结果交给现有执行引擎和运行表

对当前项目来说，最合适的落地方式就是在 `runtime` 下新增 `schedule` 包，作为一个独立但与现有 PiFlow 执行链紧密衔接的子系统来实现。
