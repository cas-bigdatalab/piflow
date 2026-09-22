---
name: corpus_dataset_sample
description: |
  Corpus 语料采样源节点。直接调用固定的 Corpus HTTP 服务 `corpus.dataset.sampler` 接口，根据数据集 CSTR 随机采样指定数量的语料，并将接口响应保存为 JSON 文件。

  本 Skill 是 source node，不接收上游 DAG 文件或数据流；数据集 CSTR 和采样数量由节点参数直接配置。

  当用户需要从 Corpus 数据集随机抽取少量语料进行查看、验证或调试时使用此 Skill。
name_zh: 语料采样源节点
input_params:
  - name: cstr
    type: string
    required: true
    description: 数据集 CSTR 标识
  - name: size
    type: int
    required: false
    default: 5
    description: 随机采样条数
  - name: output
    type: string
    required: false
    default: corpus_dataset_sample_output.json
    description: 输出 JSON 文件路径
output_params:
  - name: output
    type: json_file
    description: Corpus 数据集随机采样接口响应 JSON 文件
tag: 语料采样
disciplinary_field: 语料采样
publisher: COMMUNITY
---

## 功能概述

该 Skill 用于从指定 Corpus 数据集随机采样语料。脚本直接向 `http://172.31.3.81:7005/corpus.dataset.sampler` 发送 `GET` 请求，并通过查询参数传递 `cstr` 和 `size`。

这是一个 source node：没有上游 DAG 输入，但必须在节点参数中配置目标数据集的 `cstr`，采样数量可按需要调整。执行完成后，完整接口响应会保存到 JSON 文件并打印输出路径。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| cstr | string | 是 | - | 数据集 CSTR 标识，例如 `dataset_001` |
| size | int | 否 | 5 | 随机采样条数，必须大于 0 |
| output | string | 否 | `corpus_dataset_sample_output.json` | 输出 JSON 文件路径 |

## 请求接口

```text
GET http://172.31.3.81:7005/corpus.dataset.sampler?cstr={cstr}&size={size}
Accept: */*
```

## 输出数据格式

```json
{
  "success": true,
  "skill": "corpus_dataset_sample",
  "request": {"cstr": "dataset_001", "size": 5},
  "response": {"code": 200, "data": []}
}
```

`response` 保留 Corpus 上游接口的完整 JSON 响应，不改变采样记录字段。请求失败时输出 `success: false` 和 `error` 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_corpus_dataset_sample.py \
  --cstr dataset_001

python scripts/run_corpus_dataset_sample.py \
  --cstr dataset_001 --size 20 \
  --output outputs/dataset_sample.json
```

### 参数说明

- `--cstr`：数据集 CSTR 标识，必填且不能为空。
- `--size`：随机采样条数，默认 `5`，必须为正整数。
- `--output`：输出 JSON 文件路径，默认 `corpus_dataset_sample_output.json`。

## 注意事项

1. 该 Skill 不读取上游文件，`cstr` 和 `size` 来自节点自身配置。
2. 随机采样由 Corpus 上游服务执行，Skill 不在本地重复采样。
3. 需要运行环境能够访问 `172.31.3.81:7005`。
4. 请求超时、HTTP 错误或非 JSON 响应都会写入错误结果，并以非零状态退出。
