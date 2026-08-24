---
name: corpus_dataset_source_stop
description: |
  Corpus 数据集输入源算子。用于根据数据集唯一标识 ID 查询数据集详情，取出其中的 cstr，再获取该数据集的下载地址集合，
  将选定的数据集文件下载到当前 PiFlow workspace，并以固定输出 key output 的 FileArtifact 形式输出给下游算子。
  当任务需要通过数据集唯一标识 ID 拉取一个或多个 tar 文件，并让下游节点直接消费本地文件路径时使用此 skill。
  该算子没有上游输入，必须作为 DAG 的起始节点使用。
name_zh: Corpus 数据集输入源算子
input_params:
  - name: dataset_id
    type: string
    required: true
    description: 数据集唯一标识 ID
  - name: fileName
    type: string
    required: false
    description: 可选，指定要输出的文件名；不传则默认取第一个文件
output_params:
  - name: "output"
    type: file_artifact
    description: 固定输出 key output，对应下载后的本地文件 FileArtifact
tag: 输入
publisher: COMMUNITY
---

# corpus_dataset_source_stop

用于作为 DAG 的起始节点，根据 `dataset_id` 查询 corpus 数据集详情，取出其中的 `cstr` 后再获取下载地址集合，选择并下载一个文件到当前 workspace，通过固定的 `output` 输出槽位提供给下游节点。

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

4. 解析返回的 `data` 数组。当前响应中每个元素是一个连接器副本对象，下载地址位于 `downloadUrls` 数组中：

```json
{
  "data": [
    {
      "downloadUrls": [
        "http://10.0.82.213:7004/corpus.dataset.file.download/ES-CORPUS-B138/es-corpus-b138.tar"
      ],
      "name": "连接器节点1"
    }
  ]
}
```

实现会按 `data` 顺序、再按 `downloadUrls` 顺序展开地址，并选择第一个文件下载。若传入 `fileName`，则优先匹配对应文件；同时兼容旧版直接返回 URL 字符串数组的格式。每个 URL 的文件名取自 URL 末尾路径：

- `fileName`
- `downloadUrl`

5. 将选中的下载地址下载到当前任务专属目录：

```text
workspace/<process_id>/<stop_name>_<job_id>_<random>/output/<fileName>
```

6. 输出：

```text
output -> FileArtifact(path="<workspace-local-path>")
```

下游算子通过 `artifact.path` 使用本地文件，不直接消费远程 URL。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `dataset_id` | string | 是 | 数据集唯一标识 ID |

## 输出约定

该 Stop 固定只输出一个 `output` 端口。

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
3. 下载地址来自 `/dataset/downloadDatasetFileUrls/{cstr}` 返回的 `data[*].downloadUrls`，默认取展开后的第一个有效 URL。
4. `fileName` 只用于选择下载哪一个文件，不再作为输出 key。
5. 该 Stop 只负责下载，不负责自动解压；解压应由下游专门算子完成。
