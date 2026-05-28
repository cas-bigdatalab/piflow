---
name: pdf_metadata_extract_restored
description: "提取 PDF 文件元数据并输出 JSON 结果。 当用户提到把这次流程沉淀成 skill、保存为 skill等需求时使用此 skill。"
version: 1.0.0
name_zh: "PDF 元数据提取回调算子"
category: document_processing
tag: "输入"
metadata:
  entry_chain: callback_distillation
  verified: true
  restored_from_flow: true
  flow_task_name: "PDF 元数据提取"
  flow_success_evidence:
    output_path: workspace/outputs/pdf_metadata_extract_output.json
input_params:
  - name: input_path
    type: string
    role: input_data
    description: "输入 PDF 文件路径"
    required: true
output_params:
  - name: output_path
    type: json_file
    role: output_data
    description: "输出 JSON 文件路径"
---

# PDF 元数据提取 技能

## 功能说明

提取 PDF 文件元数据并输出 JSON 结果。 当用户提到把这次流程沉淀成 skill、保存为 skill等需求时使用此 skill。

## 触发条件

- 技能类别：document_processing
- DAG 类型：输入
- 当用户提到“把这次流程沉淀成 skill”时优先考虑使用此技能。
- 当用户提到“保存为 skill”时优先考虑使用此技能。
- 当一次真实处理流程已经跑通，并且用户希望将其封装为可复用 skill 时使用此技能。
- 当现有技能库无法直接满足需求，但已经通过脚本或步骤成功完成任务，并希望回调式沉淀为 skill 时使用此技能。

## 核心功能

- 提取 PDF 元数据
- 复用已验证成功的处理脚本
- 输出 JSON 结果

## 处理逻辑

- 读取输入 PDF 文件
- 提取标题、作者、主题、页数和日期等元数据
- 输出为 JSON 文件

## 支持的文件格式

- 输入：.pdf
- 输出：.json

## 使用方法

```bash
python scripts/run_pdf_metadata_extract.py --input_path <input_path>
```

## 参数说明

| 参数 | 类型 | 角色 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| input_path | string | input_data | 是 | - | 输入 PDF 文件路径 |

## 输出参数

| 参数 | 类型 | 角色 | 默认值 | 说明 |
|------|------|------|--------|------|
| output_path | json_file | output_data | - | 输出 JSON 文件路径 |

## 示例

### 从成功流程恢复 skill 后的典型调用

```bash
python scripts/run_pdf_metadata_extract.py --input_path workspace/temp/document.pdf --output_path workspace/outputs/pdf_metadata_extract_output.json
```

## 输出结构

```json
{
  "output_path": "workspace/outputs/pdf_metadata_extract_output.json"
}
```

## 输出示例

```json
{
  "output_path": "workspace/outputs/pdf_metadata_extract_output.json"
}
```

## 注意事项

- 本 skill 草稿由已验证成功的处理流程恢复生成，建议人工补齐命名、图标与触发表达。
- 在回调式沉淀链路中，应优先复用已有脚本和成功证据，而不是重新手写实现。
