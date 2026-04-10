---
name: entity_attribute_aggregator
description: |
  实体属性聚合工具。从多个文档中提取并总结给定实体的特定属性信息。
  当用户提到从文档中提取实体信息、总结人物属性、聚合实体特征、提取文档中的实体信息、
  根据文档总结实体属性（如总结某人物的主要经历、身份背景、成就等）等需求时使用此skill。
  即使用户没有明确说出"聚合"或"实体"，只要任务涉及从多个文档中提取和总结某个主题/人物/实体的
  特定属性，就应该使用此skill。
---

# Entity Attribute Aggregator 实体属性聚合 Skill

## 功能概述

本skill通过调用大语言模型（LLM）API，从多个相关文档中智能提取并总结给定实体的特定属性信息。
例如：从多篇关于李莲花的文档中总结其"身份背景"或"主要经历"。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 从多个文档中提取实体信息
- 总结某人物/实体的属性（如身份背景、主要经历、成就等）
- 聚合分散在不同文档中的实体特征
- 根据文档内容生成实体画像
- 文档信息抽取与整合

## 核心参数说明

### 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--api_model` | 调用的LLM模型名称 | `qwen2.5-72b-instruct`, `gpt-4o` |
| `--entity` | 要提取属性的实体名称 | `李莲花`, `孙悟空` |
| `--attribute` | 要提取的属性名称 | `身份背景`, `主要经历`, `另外身份` |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input_key` | 输入文档的键名 | `event_description` |
| `--output_key` | 输出结果的键名 | `entity_attribute` |
| `--word_limit` | 输出字数限制 | `100` |
| `--max_token_num` | 输入文档的最大token数 | `None` (无限制) |
| `--api_endpoint` | API端点URL | `None` |
| `--example_prompt` | 示例提示词 | `None` |

## 输入文件格式

输入为JSON文件，支持两种格式：

**格式1：单条数据**
```json
{
  "meta": [
    {"event_description": "文档内容1"},
    {"event_description": "文档内容2"}
  ]
}
```

**格式2：多条数据**
```json
[
  {
    "meta": [
      {"event_description": "文档内容1"},
      {"event_description": "文档内容2"}
    ]
  }
]
```

## 使用方法

### 步骤1：准备输入数据

确保文档内容存储在JSON文件的 `meta` 字段下，每个文档使用 `--input_key` 指定的键名（默认 `event_description`）。

### 步骤2：执行聚合脚本

```bash
python scripts/run_entity_attribute_aggregator.py \
  --input <输入JSON文件路径> \
  --output <输出JSON文件路径> \
  --api_model <模型名称> \
  --entity <实体名称> \
  --attribute <属性名称> \
  [--word_limit <字数限制>]
```

### 步骤3：获取结果

脚本执行完成后，输出文件包含聚合后的属性总结。

## 命令行参数速查

```bash
python scripts/run_entity_attribute_aggregator.py \
  --input ./input.json \
  --output ./output.json \
  --api_model qwen2.5-72b-instruct \
  --entity 李莲花 \
  --attribute 身份背景 \
  --word_limit 100
```

## 输出示例

**输出JSON格式：**
```json
{
  "entity_attribute": "# 李莲花\n## 身份背景\n..." 
}
```

**命令行输出：**
```
[OK] Entity attribute aggregation completed!
   Entity: 李莲花
   Attribute: 身份背景
   Input file: ./input.json
   Output file: ./output.json
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer，可用以下指令进行安装：
```bash
pip install py-data-juicer
```

**API配置：**
使用此skill前，需要设置以下环境变量：
```bash
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/
export OPENAI_API_KEY=your_api_key
```

## 注意事项

1. **必需参数**： `--api_model`, `--entity`, `--attribute` 是必需参数
2. **输入格式**：输入JSON必须包含 `meta` 字段
3. **API配置**：确保环境变量中配置了正确的API端点和密钥
4. **输出路径**：脚本会自动创建输出目录
5. **字数限制**：默认100字，可通过 `--word_limit` 调整
