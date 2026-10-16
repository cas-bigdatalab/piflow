---
name: corpus_dataset_directory
description: |
  查看数据内容源节点。直接调用固定的数据集 HTTP 服务 `metacat.file.dir.query` 接口，根据数据集 CSTR 获取数据内容根层，或根据目录节点 `fileId` 获取下一层内容，并将接口响应保存为 JSON 文件。

  本 Skill 是 source node，不接收上游 DAG 文件或数据流；数据集 CSTR 和可选目录节点 ID 由节点参数直接配置。

  当用户需要查看数据内容、浏览内容目录、展开目录节点或获取内容树的某一层时使用此 Skill。
name_zh: 查看数据内容
input_params:
  - name: cstr
    type: string
    required: true
    description: 数据集 CSTR 标识
  - name: file_id
    type: string
    required: false
    description: 要展开的目录节点 fileId；不传时获取目录根层
  - name: output
    type: string
    required: false
    default: corpus_dataset_directory_output.json
    description: 输出 JSON 文件路径
output_params:
  - name: output
    type: json_file
    description: 数据集目录接口响应 JSON 文件
tag: 查看数据内容
disciplinary_field: 数据内容查看
publisher: COMMUNITY
---

## 功能概述

该 Skill 用于查看数据集内容结构。脚本向 `http://172.31.3.81:7005/metacat.file.dir.query` 发送 `GET` 请求，通过查询参数传递 `cstr`；传入 `file_id` 时，同时传递 `fileId`，获取该内容节点的下一层。

这是一个 source node：没有上游 DAG 输入，必须在节点参数中配置 `cstr`。首次请求不传 `file_id` 获取根层；目录响应中的 `isFile: false` 节点可将其 `fileId` 作为下一次请求的 `file_id`，`isFile: true` 表示文件叶子节点。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|--------|--------|------|
| cstr | string | 是 | - | 数据集 CSTR 标识，例如 `1928844366999224320` |
| file_id | string | 否 | 无 | 要展开的目录节点 ID；不传时查询目录根层 |
| output | string | 否 | `corpus_dataset_directory_output.json` | 输出 JSON 文件路径 |

## 请求接口

根目录：

```text
GET http://172.31.3.81:7005/metacat.file.dir.query?cstr={cstr}
```

展开节点：

```text
GET http://172.31.3.81:7005/metacat.file.dir.query?cstr={cstr}&fileId={file_id}
```

## 输出数据格式

```json
{
  "success": true,
  "skill": "corpus_dataset_directory",
  "request": {"cstr": "1928844366999224320", "file_id": "4003697"},
  "response": {"code": 200, "data": []}
}
```

`response` 保留上游接口的完整 JSON 响应，不改变目录节点字段。请求失败时输出 `success: false` 和 `error` 字段。

## 使用示例

```bash
python scripts/run_corpus_dataset_directory.py \
  --cstr 1928844366999224320

python scripts/run_corpus_dataset_directory.py \
  --cstr 1928844366999224320 \
  --file_id 4003697 \
  --output outputs/dataset_directory.json
```

## 注意事项

1. 该 Skill 不读取上游文件，`cstr` 和 `file_id` 来自节点自身配置。
2. `file_id` 会映射为上游接口的 `fileId` 参数。
3. 查询参数由 HTTP 客户端编码，不需要手工拼接 URL 转义字符。
4. 需要运行环境能够访问 `172.31.3.81:7005`。
5. 请求超时、HTTP 错误或非 JSON 响应都会写入错误结果，并以非零状态退出。
