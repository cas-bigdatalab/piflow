---
name: corpus_dataset_search
description: |
  数据集检索源节点。直接调用固定的数据集 HTTP 服务 `dataset.page` 接口，按分页和数据集元数据条件检索数据集，并将接口响应保存为 JSON 文件。

  本 Skill 是 source node，不接收上游 DAG 文件或数据流；检索条件由节点参数直接配置。

  当用户需要检索数据集、按标题或领域筛选数据集、分页查询数据集列表时使用此 Skill。
name_zh: 数据集检索
input_params:
  - name: page_num
    type: int
    required: false
    default: 1
    description: 页码，从 1 开始
  - name: page_size
    type: int
    required: false
    default: 10
    description: 每页返回的数据集数量
  - name: title
    type: string
    required: false
    description: 数据集标题筛选条件
  - name: field
    type: string
    required: false
    description: 数据集所属领域筛选条件
  - name: subject
    type: string
    required: false
    description: 数据集学科方向筛选条件
  - name: author
    type: string
    required: false
    description: 数据集作者筛选条件
  - name: doi
    type: string
    required: false
    description: 数据集 DOI 筛选条件
  - name: output
    type: string
    required: false
    default: corpus_dataset_search_output.json
    description: 输出 JSON 文件路径
output_params:
  - name: output
    type: json_file
    description: 数据集分页接口的检索结果 JSON 文件
tag: 数据集检索
disciplinary_field: 数据集检索
publisher: COMMUNITY
---

## 功能概述

该 Skill 用于检索数据集列表。脚本直接向 `http://172.31.3.81:7005/dataset.page` 发送 `POST` 请求，将分页参数放在 URL 查询参数中，将筛选条件放在 JSON 请求体中。

这是一个 source node：没有上游 DAG 输入，但可以在节点配置中填写分页和筛选参数。脚本完成请求后，将请求信息和完整上游响应写入 JSON 文件，并在终端打印输出文件路径。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page_num | int | 否 | 1 | 页码，从 1 开始 |
| page_size | int | 否 | 10 | 每页返回数量 |
| title | string | 否 | 无 | 数据集标题筛选条件 |
| field | string | 否 | 无 | 数据集所属领域筛选条件 |
| subject | string | 否 | 无 | 数据集学科方向筛选条件 |
| author | string | 否 | 无 | 数据集作者筛选条件 |
| doi | string | 否 | 无 | 数据集 DOI 筛选条件 |
| output | string | 否 | `corpus_dataset_search_output.json` | 输出 JSON 文件路径 |

## 请求接口

```text
POST http://172.31.3.81:7005/dataset.page?pageNum={page_num}&pageSize={page_size}
Content-Type: application/json
```

未填写的筛选参数不会写入请求体。示例请求体：

```json
{"title": "锂电池", "field": "材料科学"}
```

## 输出数据格式

输出为 JSON 文件，每次运行覆盖目标文件：

```json
{
  "success": true,
  "skill": "corpus_dataset_search",
  "request": {"page_num": 1, "page_size": 10, "title": "锂电池"},
  "response": {"code": 200, "data": []}
}
```

`response` 保留上游接口的完整 JSON 响应。请求失败时 `success` 为 `false`，并写入 `error` 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_corpus_dataset_search.py

python scripts/run_corpus_dataset_search.py \
  --page_num 1 --page_size 10 \
  --title 锂电池 --field 材料科学 \
  --output outputs/corpus_search.json
```

### 参数说明

- `--page_num`：页码，必须大于等于 1，默认 `1`。
- `--page_size`：每页数量，默认 `10`。
- `--title`、`--field`、`--subject`、`--author`、`--doi`：可选筛选条件。
- `--output`：输出文件路径，默认 `corpus_dataset_search_output.json`。

## 注意事项

1. 该 Skill 不读取上游文件，所有检索条件来自节点自身参数。
2. 需要运行环境能够访问 `172.31.3.81:7005`。
3. 请求超时、HTTP 错误或非 JSON 响应都会写入错误结果，并以非零状态退出。
