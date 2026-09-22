---
name: corpus_dataset_preview
description: |
  数据集预览源节点。直接调用固定的数据集 HTTP 服务 `corpus.dataset.preview` 接口，根据数据集 CSTR 获取数据集预览结果，并将接口响应保存为 JSON 文件。

  本 Skill 是 source node，不接收上游 DAG 文件或数据流；数据集 CSTR 由节点参数直接配置。

  当用户需要预览数据集内容时使用此 Skill。
name_zh: 数据集预览源节点
input_params:
  - name: cstr
    type: string
    required: true
    description: 数据集 CSTR 标识
  - name: output
    type: string
    required: false
    default: corpus_dataset_preview_output.json
    description: 输出 JSON 文件路径
output_params:
  - name: output
    type: json_file
    description: 数据集预览接口响应 JSON 文件
tag: 数据集预览
disciplinary_field: 数据集预览
publisher: COMMUNITY
---

## 功能概述

该 Skill 用于获取数据集的预览结果。脚本直接向 `http://172.31.3.81:7005/corpus.dataset.preview` 发送 `GET` 请求，并通过查询参数传递数据集 CSTR。

这是一个 source node：没有上游 DAG 输入，但必须在节点参数中配置目标数据集的 `cstr`。执行完成后，完整接口响应会保存到 JSON 文件并打印输出路径。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| cstr | string | 是 | - | 数据集 CSTR 标识，例如 `dataset_001` |
| output | string | 否 | `corpus_dataset_preview_output.json` | 输出 JSON 文件路径 |

## 请求接口

```text
GET http://172.31.3.81:7005/corpus.dataset.preview?cstr={cstr}
Accept: */*
```

## 输出数据格式

```json
{
  "success": true,
  "skill": "corpus_dataset_preview",
  "request": {"cstr": "dataset_001"},
  "response": {"code": 200, "data": {}}
}
```

`response` 保留上游接口的完整 JSON 响应，不对预览字段进行二次转换。请求失败时输出 `success: false` 和 `error` 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_corpus_dataset_preview.py \
  --cstr dataset_001

python scripts/run_corpus_dataset_preview.py \
  --cstr dataset_001 \
  --output outputs/dataset_preview.json
```

### 参数说明

- `--cstr`：数据集 CSTR 标识，必填且不能为空。
- `--output`：输出 JSON 文件路径，默认 `corpus_dataset_preview_output.json`。

## 注意事项

1. 该 Skill 不读取上游文件，`cstr` 来自节点自身配置。
2. 查询参数由 HTTP 客户端编码，不需要手工拼接 URL 转义字符。
3. 需要运行环境能够访问 `172.31.3.81:7005`。
4. 请求超时、HTTP 错误或非 JSON 响应都会写入错误结果，并以非零状态退出。
