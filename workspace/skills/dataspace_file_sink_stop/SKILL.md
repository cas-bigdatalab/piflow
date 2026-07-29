---
name: dataspace_file_sink_stop
description: Dataspace 文件输出终止算子。用于接收上游算子的单个文件输出，按指定相对路径上传到 Dataspace 空间目录中。该算子必须作为 DAG 的终止节点使用。
name_zh: Dataspace 文件输出终止算子
input_params:
  - name: input
    type: string
    required: true
    description: 上游算子的文件输出引用
  - name: datasource_id
    type: string
    required: true
    description: Dataspace 数据源实例 ID
  - name: relative_path
    type: string
    required: true
    description: 上传到 Dataspace 时使用的空间内相对文件路径
  - name: overwrite
    type: bool
    required: false
    default: false
    description: 本地托管目录中存在同名文件时是否允许覆盖
  - name: output
    type: string
    required: true
    description: 上传后保留的本地文件输出路径
output_params:
  - name: output
    type: string
    description: 已托管并上传的本地文件引用
tag: 输出
publisher: COMMUNITY
---

# dataspace_file_sink_stop

用于作为 DAG 的终止节点，接收上游文件输出，将文件托管到本地受控目录后上传到 Dataspace 指定目录，并保留 `output` 结果引用。

## 使用方式

```bash
python scripts/run_dataspace_file_sink_stop.py \
  --input <input> \
  --datasource_id <datasource_id> \
  --relative_path <relative_path> \
  --overwrite <overwrite> \
  --output <output>
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `input` | string | 是 | 上游算子的文件输出引用 |
| `datasource_id` | string | 是 | Dataspace 数据源实例 ID |
| `relative_path` | string | 是 | 上传到 Dataspace 时使用的空间内相对文件路径 |
| `overwrite` | bool | 否 | 本地托管目录中存在同名文件时是否允许覆盖 |
| `output` | string | 是 | 上传后保留的本地文件输出路径 |

## 注意事项

1. 该算子应放在流程末端，用于上传结果文件。
2. 脚本内部会先在本地托管目录构造目标路径，再整体上传到 Dataspace。
3. `output` 会保留一份本地文件供流程结果继续引用。
