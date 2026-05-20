---
name: most_relevant_entities_aggregator
description: |
  最相关实体聚合工具。从文档中提取与给定实体最相关的指定类型实体，并按重要性排序。
  当用户提到提取相关人物、查找相关实体、排序实体、分析实体关系、提取主要角色等需求时使用此skill。
  即使用户没有明确说出"最相关实体"，只要任务涉及从文档中分析并提取与目标相关的实体，
  就应该使用此skill。

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

  - name: entity
    type: string
    required: true
    description: 要查询的实体名称

  - name: query_entity_type
    type: string
    required: true
    description: 要查询的相关实体类型（如人物、地点、组织）

  - name: input_key
    type: string
    required: false
    default: event_description
    description: 输入文档的键名

  - name: output_key
    type: string
    required: false
    default: most_relevant_entities
    description: 输出结果的键名

  - name: max_token_num
    type: int
    required: false
    description: 输入文档的最大token数

  - name: api_endpoint
    type: string
    required: false
    description: API端点URL

output_params:
  - name: output
    type: json_file
    description: 实体聚合后的JSON文件，包含按重要性排序的相关实体列表
---

# Most Relevant Entities Aggregator 最相关实体聚合 Skill

## 功能概述

本skill通过调用大语言模型（LLM）API，从多个相关文档中智能识别并提取与指定实体最相关的特定类型实体。
例如：从多篇武侠小说片段中提取与"李莲花"最相关的"人物"，并按重要性排序。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 提取相关实体
- 查找相关人物
- 分析实体关系
- 提取主要角色
- 实体排序分析
- 关联实体提取

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |
| `--api_model` | API模型名称 |
| `--entity` | 要查询的实体名称 |
| `--query_entity_type` | 要查询的相关实体类型 (如 人物、地点、组织) |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input_key` | 输入文档的键名 | `event_description` |
| `--output_key` | 输出结果的键名 | `most_relevant_entities` |
| `--max_token_num` | 输入文档的最大token数 | `None` |
| `--api_endpoint` | API端点URL | `None` |

## 输入文件格式

```json
{
  "meta": [
    {"event_description": "文档内容1"},
    {"event_description": "文档内容2"},
    {"event_description": "文档内容3"}
  ]
}
```

或自定义键名：

```json
{
  "meta": [
    {"events": "文档内容1"},
    {"events": "文档内容2"}
  ]
}
```

## 使用方法

```bash
# 基本用法
python scripts/run_most_relevant_entities_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --entity 李莲花 \
  --query_entity_type 人物

# 自定义输入输出键名
python scripts/run_most_relevant_entities_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --entity 李莲花 \
  --query_entity_type 人物 \
  --input_key events \
  --output_key relevant_roles

# 限制token数量
python scripts/run_most_relevant_entities_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --entity 李莲花 \
  --query_entity_type 人物 \
  --max_token_num 100
```

## 输出示例

**命令行输出：**
```
[OK] Most relevant entities aggregation completed!
   Entity: 李莲花
   Query entity type: 人物
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {
    "most_relevant_entities": ["李相夷", "笛飞声", "单孤刀", "方多病"]
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

1. **必需参数**：需要指定 `--api_model`、`--entity` 和 `--query_entity_type`
2. **输入格式**：输入JSON必须包含 `meta` 字段
3. **输出排序**：结果按重要性从高到低排序
4. **实体类型**：可指定任意实体类型，如"人物"、"地点"、"组织"、"事件"等
