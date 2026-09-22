---
name: corpus_dataset_detail
description: |
  Corpus 语料访问源节点。直接调用固定的 Corpus HTTP 服务 `dataset/{cstr}` 接口，根据数据集 CSTR 获取数据集详情，并将接口响应保存为 JSON 文件。

  本 Skill 是 source node，不接收上游 DAG 文件或数据流；数据集 CSTR 由节点参数直接配置。

  当用户需要查看 Corpus 数据集的完整元数据和详情时使用此 Skill。
name_zh: 语料访问源节点
input_params:
  - name: cstr
    type: string
    required: true
    description: 数据集 CSTR 标识
  - name: output
    type: string
    required: false
    default: corpus_dataset_detail_output.json
    description: 输出 JSON 文件路径
output_params:
  - name: output
    type: json_file
    description: Corpus 数据集详情接口响应 JSON 文件
tag: 语料访问
publisher: COMMUNITY
---

## 功能概述

该 Skill 用于根据数据集 CSTR 获取 Corpus 数据集详情。脚本直接向 `http://172.31.3.81:7005/dataset/{cstr}` 发送 `GET` 请求，并将完整响应保存为 JSON 文件。

这是一个 source node：没有上游 DAG 输入，但必须在节点参数中配置目标数据集的 `cstr`。执行完成后脚本会打印输出文件路径，供下游节点或用户读取。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| cstr | string | 是 | - | 数据集 CSTR 标识，例如 `ST001-CAMPBELL-B001` |
| output | string | 否 | `corpus_dataset_detail_output.json` | 输出 JSON 文件路径 |

## 请求接口

```text
GET http://172.31.3.81:7005/dataset/{cstr}
Accept: */*
```

## 输出数据格式

```json
{
  "success": true,
  "skill": "corpus_dataset_detail",
  "request": {"cstr": "ST001-CAMPBELL-B001"},
  "response": {"code": 200, "data": {}}
}
```

`response` 保留 Corpus 上游接口的完整 JSON 响应。请求失败时输出 `success: false` 和 `error` 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_corpus_dataset_detail.py \
  --cstr ST001-CAMPBELL-B001

python scripts/run_corpus_dataset_detail.py \
  --cstr ST001-CAMPBELL-B001 \
  --output outputs/dataset_detail.json
```

### 参数说明

- `--cstr`：数据集 CSTR 标识，必填且不能为空。
- `--output`：输出 JSON 文件路径，默认 `corpus_dataset_detail_output.json`。

## 注意事项

1. 该 Skill 不读取上游文件，`cstr` 来自节点自身配置。
2. CSTR 会进行 URL 路径编码，避免特殊字符破坏请求路径。
3. 需要运行环境能够访问 `172.31.3.81:7005`。
4. 请求超时、HTTP 错误或非 JSON 响应都会写入错误结果，并以非零状态退出。
