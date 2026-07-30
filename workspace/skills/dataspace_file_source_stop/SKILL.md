---
name: dataspace_file_source_stop
description: Dataspace 文件输入源算子。用于根据 Dataspace 数据源实例 ID 和空间内文件路径下载单个文件，并将该文件作为工作流输入提供给下游算子。该算子没有上游输入，必须作为 DAG 的起始节点使用。
name_zh: Dataspace文件输入源算子
input_params:
  - name: datasource_id
    type: string
    required: true
    description: Dataspace 数据源实例 ID
  - name: input_file_path
    type: string
    required: true
    description: 需要下载的 Dataspace 空间内文件路径，允许以 / 开头
  - name: output
    type: string
    required: true
    description: 下载后的本地文件输出路径
output_params:
  - name: output
    type: string
    description: 下载后的本地文件引用，提供给下游算子使用
tag: 输入
publisher: COMMUNITY
---

# dataspace_file_source_stop

用于作为 DAG 的起始节点，从 Dataspace 空间下载指定文件，并向下游节点暴露 `output` 输出槽位供引用。

## 使用方式

```bash
python scripts/run_dataspace_file_source_stop.py \
  --datasource_id <datasource_id> \
  --input_file_path <input_file_path> \
  --output <output>
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `datasource_id` | string | 是 | Dataspace 数据源实例 ID |
| `input_file_path` | string | 是 | 需要下载的 Dataspace 空间内文件路径，允许以 `/` 开头 |
| `output` | string | 是 | 下载后的本地文件输出路径 |

## 注意事项

1. 该算子没有上游输入，适合作为流程起点。
2. 脚本内部会自动去掉 `input_file_path` 前导 `/`，再调用服务层完成 Dataspace 文件下载。
3. `output` 会被强制写出，供下游普通 skill 继续消费。
