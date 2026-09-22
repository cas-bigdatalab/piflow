# Cross DAG 四个 Demo 缓存

仅为四个固定演示请求启用。配置在 `config/cross_dag_demo_cache.json`，当前 `enabled: true`。预测智能体、数据目录过滤、模型配置及其他请求的处理逻辑不变。

## 怎么使用

1. 部署代码并重启服务。
2. 通过现有会话界面，依次提交配置文件中的四条原文，正常确认执行。第一个地震目录、第二个化学语料、第三个地学打包、第四个比表面积比较分别建立缓存。
3. 首次仍真实规划、绑定和执行。页面轮询任务状态，确认 `SUCCESS` 且结果可下载时，后端自动下载一份真实文件并保存缓存，不需要手动下载来触发。
4. 后续提交相同原文，规划阶段复用方案；确认执行后复用结果和文件，跳过远端执行。可以换会话，服务重启后也可复用。

只忽略空白字符差异；改了实质文字、数字、文件名或标点，就是普通请求，不做语义模糊匹配。第二个 Demo 若选择不同的候选数据集，会分别建立结果缓存，不能串用文件。

## 两层缓存与失败处理

| 阶段 | 首次 | 命中后 |
|---|---|---|
| 预绑定方案 | 原有意图解析、规划和校验；保存首份校验通过且可继续的方案 | 恢复方案，生成新的任务和计划 ID，仍等待确认执行 |
| 执行结果 | 原有绑定和执行；任务成功、文件完整下载后才发布缓存 | 生成当前用户所属的新过程 ID，直接完成，沿用历史记录、状态查询和下载接口 |

缓存不保存失败结果。仅提交成功、还在运行、结果文件不存在或下载失败，都不算结果缓存完成；后续会继续尝试。若只有方案缓存，则复用方案并正常执行。文件损坏或丢失时，新任务恢复真实执行。

首次保存结果需要额外下载和本地存储文件，因此首次成功状态查询可能更慢。缓存写入失败只记录日志，不改变原任务的执行结果。缓存使用原有文件锁依赖 `filelock`，按项目依赖安装即可。

缓存命中会返回 `cache_hit: true`、`cache_created_at`；流中有 `cache_plan` / `cache_result` 阶段，说明已复用结果，不模拟重新计算的过程。原有响应字段和下载鉴权保留。

缓存复用的是首次成功时的数据与结果，不随上游数据变化自动更新。演示数据更新或希望重新计算时，按下文清除缓存。

## 接口范围

会话流程的以下原生接口接入缓存，其对应的 `/api/piflow/v1/agents` 入口自动生效，前端调用方式不用改：

- `POST /api/piflow/v1/xdc/sessions/{session_id}/tasks/plan/pre-bind/stream`
- `POST /api/piflow/v1/xdc/tasks/{task_id}/bind-and-execute/stream`
- `GET /api/piflow/v1/xdc/tasks/{task_id}/execution/status`：首次成功时保存结果缓存。
- `GET /api/piflow/v1/xdc/execution/{process_id}/status`、`GET .../download`：支持新生成的缓存过程 ID。

请继续按执行响应中的 `status_url` 轮询任务，直到结束；只轮询过程级 `process_status_url` 不会触发首次结果保存。旧的无会话规划接口没有接入这项 Demo 缓存。

## 存在哪里

`<项目配置的 workspace>/cross_dag_demo_cache/`：

- `entries/`：四个 Demo 的方案、执行草稿和结果索引。
- `objects/`：完整结果文件和元数据。已有任务通过独立对象读取文件。

不新增数据库表。复用现有会话、任务、执行记录表；缓存过程 ID 以 `xdc-demo-` 开头，与真实远端任务区分。部署时需保留 workspace；多个服务实例若要共享同一份缓存，应共享该缓存目录。

## 关闭或重新生成

**关闭后续缓存：** 把配置文件的 `enabled` 改成 `false`。按请求读取配置，无需修改智能体代码；已生成的缓存任务仍可以下载文件。

**重新生成：** 在项目根目录、使用服务的 Python 环境执行。先停止正在进行的四个 Demo 请求，避免清除与首次写入同时发生。

```bash
# 清除四个 Demo 的查询索引，下一次重新真实运行
python -m services.cross_dag_demo_cache --clear all

# 或只清除其中一个
python -m services.cross_dag_demo_cache --clear earthquake
python -m services.cross_dag_demo_cache --clear chemistry
python -m services.cross_dag_demo_cache --clear earth_bundle
python -m services.cross_dag_demo_cache --clear surface_area
```

命令保留 `objects/`，确保历史缓存任务仍能下载；不会清除原数据、数据库或其他缓存。也可以增加配置的 `version` 开启一批新缓存，旧任务的下载仍保留。

## 修改边界

- 新增独立模块 `services/cross_dag_demo_cache.py`、上述配置、本说明及测试。
- `services/xdc_session_service.py`：仅增加四条原文的缓存入口和成功后的保存钩子。
- `services/cross_dag_service.py`：仅在原有权限检查之后识别缓存过程的状态与下载。
- 不修改意图解析、规划算法、副本选择、执行引擎、数据源、预测智能体或前端。
