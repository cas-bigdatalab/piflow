---
name: nested_aggregator
description: |
  嵌套聚合工具。将多个文档碎片整合成一个连贯的文档总结。
  当用户提到文档摘要、整合文档、文档聚合、碎片整合、长文总结等需求时使用此skill。
  即使用户没有明确说出"嵌套"或"聚合"，只要任务涉及将多个短文档整合成一个总结，
  就应该使用此skill。
---

# Nested Aggregator 嵌套聚合 Skill

## 功能概述

本skill通过调用大语言模型（LLM）API，将多个分散的文档碎片智能整合成一个连贯的文档总结。
适用于处理长文档分段后的聚合、多个相关片段的整合等场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 文档摘要
- 整合文档
- 文档聚合
- 碎片整合
- 长文总结
- 多段合一

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |
| `--api_model` | API模型名称 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input_key` | 输入文档的键名 | `event_description` |
| `--output_key` | 输出结果的键名 | 与 input_key 相同 |
| `--max_token_num` | 每个分组最大token数 | `None` |
| `--api_endpoint` | API端点URL | `None` |

## 输入文件格式

```json
{
  "meta": [
    {"event_description": "文档碎片1内容..."},
    {"event_description": "文档碎片2内容..."},
    {"event_description": "文档碎片3内容..."}
  ]
}
```

或自定义键名：

```json
{
  "meta": [
    {"sub_docs": "文档碎片1内容..."},
    {"sub_docs": "文档碎片2内容..."},
    {"sub_docs": "文档碎片3内容..."}
  ]
}
```

## 使用方法

### 基本用法
```bash
python scripts/run_nested_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct
```

### 自定义输入键名
```bash
python scripts/run_nested_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --input_key sub_docs
```

### 限制每组token数量
```bash
python scripts/run_nested_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --max_token_num 100
```

## 输出示例

**命令行输出：**
```
[OK] Nested aggregation completed!
   API model: qwen2.5-72b-instruct
   Input key: event_description
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {
    "event_description": "整合后的完整文档总结..."
  }
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer，可用以下指令进行安装：
```bash
pip install py-data-juicer
```

**API配置：**
```bash
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/
export OPENAI_API_KEY=your_api_key
```

## 注意事项

1. **必需参数**：需要指定 `--api_model`
2. **输入格式**：输入JSON必须包含 `meta` 字段
3. **整合逻辑**：LLM会自动将多个碎片整合成连贯的总结
4. **保留信息**：会尽可能保留原文中的专有名词和关键信息
