---
name: calibrate_query_mapper
description: |
  基于参考文本校准问答对中的查询（问题）。当用户提到校准问题、校准查询、语言风格校准、问题优化等需求时使用此skill。
  即使用户没有明确说出"校准"，只要任务涉及根据参考文本调整问答对中的问题，就应该使用此skill。
---

# Calibrate Query Mapper

基于参考文本校准问答对中的查询（问题），使问题更加详细、准确，并贴合参考文本的语言风格。

本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用同以下指令进行安装：
```
pip install py-data-juicer
```

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入JSON文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |
| api_model | string | 是 | - | LLM模型名称，如 'qwen2.5-72b-instruct' |
| api_endpoint | string | 否 | - | API端点URL |
| response_path | string | 否 | choices.0.message.content | 响应内容路径 |

## 使用方法

```bash
python scripts/run_calibrate_query_mapper.py --input_path <input_path> --output_path <output_path> --api_model <model_name> [--api_endpoint <endpoint>] [--response_path <path>]
```

## 实现原理

参照测试代码 test_calibrate_query_mapper.py 中的 `_run_op` 函数：

```python
# 1. 初始化算子（必须指定api_model）
op = CalibrateQueryMapper(api_model='qwen2.5-72b-instruct')

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {
    "text": "参考文本，包含语言风格示例...",
    "query": "原始问题",
    "response": "原始回答"
  }
]
```

### 输出格式 (JSON数组)

```json
[
  {
    "text": "参考文本，包含语言风格示例...",
    "query": "校准后的问题",
    "response": "原始回答"
  }
]
```

注意：此算子只校准 query 字段，response 字段保持不变。

## 示例

```bash
python scripts/run_calibrate_query_mapper.py --input_path example_input.json --output_path output.json --api_model "qwen2.5-72b-instruct"
```

## 注意事项

- **必须设置环境变量**：使用前需设置 API key
  ```bash
  export OPENAI_API_KEY=your_api_key
  # 或
  export DASHSCOPE_API_KEY=your_api_key
  ```
- api_model 参数必须指定
- 输入数据需要包含 text（参考）、query（问题）、response（回答）三个字段
- 该算子只校准问题（query），回答（response）保持不变
- 该算子调用 LLM API，可能需要较长时间
