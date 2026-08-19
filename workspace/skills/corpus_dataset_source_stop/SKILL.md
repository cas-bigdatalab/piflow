---
name: corpus_dataset_source_stop
description: |
  Corpus 数据集输入源算子。用于根据数据集唯一标识 ID 查询数据集详情，取出其中的 cstr，再获取该数据集的下载地址集合，
  将对应的数据集文件下载到当前 PiFlow workspace，并以 fileName -> FileArtifact 的形式输出给下游算子。
  当任务需要通过数据集唯一标识 ID 拉取一个或多个 tar 文件，并让下游节点直接消费本地文件路径时使用此 skill。
  该算子没有上游输入，必须作为 DAG 的起始节点使用。
name_zh: Corpus 数据集输入源算子
input_params:
  - name: dataset_id
    type: string
    required: true
    description: 数据集唯一标识 ID
output_params:
  - name: "<fileName>"
    type: file_artifact
    description: 以返回记录中的 fileName 作为输出 key，对应下载后的本地文件 FileArtifact
tag: 输入
publisher: COMMUNITY
---

# corpus_dataset_source_stop

用于作为 DAG 的起始节点，根据 `dataset_id` 查询 corpus 数据集详情，取出其中的 `cstr` 后再获取下载地址集合，下载一个或多个文件到当前 workspace，并向下游节点暴露多个动态输出槽位。

## 行为说明

1. 请求数据集详情接口：

```text
GET {corpus_route.base_url}/dataset/queryDataset?id={dataset_id}
```

2. 从详情响应中提取：

- `cstr`
- `connectorId`
- `fromName`
- `title`
- `size`

3. 请求下载地址集合接口：

```text
GET {corpus_route.base_url}/dataset/downloadDatasetFileUrls/{cstr}
```

4. 将返回的 `data` 数组视为该数据集全部下载地址集合，并逐个下载。每个 URL 的文件名取自 URL 末尾路径：

- `fileName`
- `downloadUrl`

5. 对每个下载地址执行下载，将文件保存到当前任务专属目录：

```text
workspace/<process_id>/<stop_name>_<job_id>_<random>/output/<fileName>
```

6. 逐个输出：

```text
<fileName> -> FileArtifact(path="<workspace-local-path>")
```

下游算子通过 `artifact.path` 使用本地文件，不直接消费远程 URL。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `dataset_id` | string | 是 | 数据集唯一标识 ID |

## 输出约定

该 Stop 不固定只输出一个 `output` 端口，而是按每条元数据记录的 `fileName` 动态输出。

示例：

```text
es-corpus-b138.tar -> FileArtifact(path=".../es-corpus-b138.tar")
es-corpus-b138-extra.tar -> FileArtifact(path=".../es-corpus-b138-extra.tar")
```

每个 `FileArtifact` 会附带 metadata，当前包括：

- `datasetId`
- `cstr`
- `connectorId`
- `fromName`
- `title`
- `fileName`
- `downloadUrl`
- `size`

## 使用前提

运行时需要在配置中提供：

```yaml
corpus_route:
  base_url: "http://10.0.82.213:7003"
```

并确保该配置已经进入运行时 `settings.corpus_route.base_url`。

## 适用场景

- 通过数据集唯一标识 ID 拉取一个 corpus 数据集对应的一个或多个 tar 文件
- 下游节点只需要本地文件路径，不希望直接处理远程下载 URL
- 需要保留下载来源 metadata，便于运行日志和追踪系统记录文件来源

## 注意事项

1. 该算子是数据源 Stop，没有上游输入，适合作为流程起点。
2. 不再直接接收 `cstr` 作为输入，而是统一以数据集唯一标识 ID 为入口。
3. 下载地址来自 `/dataset/downloadDatasetFileUrls/{cstr}` 返回的 URL 集合。
4. 输出 key 使用 `fileName`，因此同一次运行中不允许出现重复的 `fileName`。
5. 该 Stop 只负责下载，不负责自动解压；解压应由下游专门算子完成。
