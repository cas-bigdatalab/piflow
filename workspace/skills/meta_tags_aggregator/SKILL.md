---
name: meta_tags_aggregator
description: |
  元标签聚合工具。合并意思相近的元标签，将多个相似标签归类到统一的标签下。
  当用户提到标签聚合、合并标签、归类标签、标签映射、标签合并、整理标签等需求时使用此skill。
  即使用户没有明确说出"聚合"或"合并"，只要任务涉及将多个相似标签归类统一，
  就应该使用此skill。

name_zh: 元标签聚合算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: api_model
    type: string
    required: true
    description: API模型名称

  - name: meta_tag_key
    type: string
    required: true
    description: 元数据标签的键名

  - name: target_tags
    type: string
    required: false
    description: 目标标签列表，逗号分隔（不指定则自动生成）

  - name: api_endpoint
    type: string
    required: false
    description: API端点URL

output_params:
  - name: output
    type: json_file
    description: 标签聚合后的JSON文件，包含合并后的标签
tag: 增强

---

# Meta Tags Aggregator 元标签聚合 Skill

## 功能概述

本skill通过调用大语言模型（LLM）API，智能分析并合并意思相近的元标签。
例如：将"开心"、"快乐"、"高兴"归类为"开心"，将"难过"、"伤心"、"悲痛"归类为"难过"。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 标签聚合
- 合并相似标签
- 归类标签
- 标签映射
- 整理标签
- 统一标签分类

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |
| `--api_model` | API模型名称 |
| `--meta_tag_key` | 元数据标签的键名 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--target_tags` | 目标标签列表，逗号分隔 | `None` (自动生成) |
| `--api_endpoint` | API端点URL | `None` |

## 输入文件格式

```json
[
  {
    "meta": [
      {"query_sentiment_label": "开心"},
      {"query_sentiment_label": "快乐"},
      {"query_sentiment_label": "难过"}
    ]
  }
]
```

或使用列表类型的标签：

```json
[
  {
    "meta": [
      {"dialog_sentiment_labels": ["开心", "平静"]},
      {"dialog_sentiment_labels": ["快乐", "开心", "幸福"]}
    ]
  }
]
```

## 使用方法

### 基本用法（自动生成标签分类）
```bash
python scripts/run_meta_tags_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --meta_tag_key query_sentiment_label
```

### 指定目标标签
```bash
python scripts/run_meta_tags_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --meta_tag_key query_sentiment_label \
  --target_tags 开心,难过,其他
```

## 输出示例

**命令行输出：**
```
[OK] Meta tags aggregation completed!
   API model: qwen2.5-72b-instruct
   Meta tag key: query_sentiment_label
   Target tags: ['开心', '难过', '其他']
   Input file: ./input.json
   Output file: ./output.json
```

**输入示例：**
```json
[{"meta": [{"query_sentiment_label": "开心"}, {"query_sentiment_label": "快乐"}, {"query_sentiment_label": "难过"}]}]
```

**输出示例：**
```json
[{"meta": [{"query_sentiment_label": "开心"}, {"query_sentiment_label": "开心"}, {"query_sentiment_label": "难过"}]}]
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

1. **必需参数**：需要指定 `--api_model` 和 `--meta_tag_key`
2. **输入格式**：输入JSON必须包含 `meta` 字段
3. **标签类型**：支持单个字符串或字符串列表作为标签值
4. **目标标签**：`--target_tags` 可选，不指定时由LLM自动生成合理的分类
