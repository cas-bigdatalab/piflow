---
name: llm_file_transform_stop
description: LLM 文件转换算子。用于读取一个文本文件，按照给定指令调用大模型进行内容转换，并输出新的文本文件。
name_zh: LLM 文件转换算子
input_params:
  - name: input
    type: string
    required: true
    description: 上游算子的文本文件输出引用
  - name: instruction
    type: string
    required: true
    description: 发送给大模型的文件转换指令
  - name: model
    type: string
    required: true
    description: 调用的大模型名称
  - name: api_key
    type: string
    required: false
    description: 大模型服务 API Key，未填写时会尝试读取环境变量 OPENAI_API_KEY
  - name: base_url
    type: string
    required: false
    default: https://api.openai.com/v1
    description: OpenAI 兼容接口地址
  - name: output_ext
    type: string
    required: false
    description: 输出文件扩展名，例如 .md、.txt；不填写时沿用输入文件扩展名
  - name: timeout_seconds
    type: number
    required: false
    default: 60.0
    description: LLM 请求超时时间，单位秒
  - name: max_input_chars
    type: integer
    required: false
    default: 100000
    description: 允许处理的最大输入字符数
  - name: max_output_tokens
    type: integer
    required: false
    description: 大模型输出 token 上限
output_params:
  - name: output
    type: string
    required: true
    description: 转换后生成的新文本文件引用
tag: LLM
node_category: system
---

# llm_file_transform_stop

用于读取一个文本文件，将文件内容和转换指令一起发送给大模型处理，并生成一个新的文本文件输出到下游。

适用场景包括：

- 文本润色
- 文档改写
- 结构化内容整理
- Markdown、JSON、CSV 等文本文件内容转换

注意事项：

- 仅支持文本类文件输入
- 如果未传 `api_key`，默认从环境变量 `OPENAI_API_KEY` 读取
- `base_url` 默认为 OpenAI 兼容接口地址
- 输出文件会保存在运行过程目录下，并作为新的文件产物继续传给下游算子
