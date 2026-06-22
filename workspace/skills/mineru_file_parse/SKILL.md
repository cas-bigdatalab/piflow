---
name: mineru_file_parse
description: |
  MinerU文件解析算子。通过远程调用MinerU接口，解析本地文件（支持PDF、DOC、PPT、Excel、图片等格式），获取文件解析结果（内容、公式、图片等），最终返回ZIP压缩包。

  本SKILL依赖requests库，请确保已安装。

name_zh: MinerU文件解析算子
input_params:
  - name: file_path
    type: string
    required: true
    description: 本地文件路径，支持PDF、DOC、PPT、Excel、图片等格式

  - name: output_zip
    type: string
    required: true
    description: 输出ZIP压缩包路径

  - name: model_version
    type: string
    required: false
    default: vlm
    description: 模型版本，默认vlm

  - name: poll_interval
    type: int
    required: false
    default: 5
    description: 轮询间隔（秒），默认5秒

  - name: timeout
    type: int
    required: false
    default: 1800
    description: 超时时间（秒），默认1800秒（30分钟）

output_params:
  - name: output_zip
    type: zip_file
    description: 解析结果ZIP压缩包

tag: 格式转换
---

## 功能概述

该算子通过远程调用MinerU API，对本地文件进行智能解析，提取文件中的文本内容、公式、图片等信息，最终将解析结果打包为ZIP压缩包返回。

## 支持的文件类型

- PDF文件（.pdf）
- Word文档（.doc, .docx）
- PowerPoint演示文稿（.ppt, .pptx）
- Excel表格（.xls, .xlsx）
- 图片文件（.jpg, .jpeg, .png, .bmp, .gif等）

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_path | string | 是 | - | 本地文件路径 |
| output_zip | string | 是 | - | 输出ZIP压缩包路径 |
| model_version | string | 否 | vlm | 模型版本 |
| poll_interval | int | 否 | 5 | 轮询间隔（秒） |
| timeout | int | 否 | 1800 | 超时时间（秒） |

## 使用示例

### 命令行调用

```bash
# 基础用法
python scripts/run_mineru_file_parse.py \
  --file_path /path/to/input.pdf \
  --output_zip /path/to/output.zip

# 指定模型版本和轮询参数
python scripts/run_mineru_file_parse.py \
  --file_path /path/to/input.docx \
  --output_zip /path/to/output.zip \
  --model_version vlm \
  --poll_interval 10 \
  --timeout 3600
```

### 参数说明

- `--file_path`: 需要解析的本地文件路径
- `--output_zip`: 解析结果ZIP压缩包的输出路径
- `--model_version`: 选择使用的模型版本，默认vlm
- `--poll_interval`: 查询解析状态的间隔时间，默认5秒
- `--timeout`: 解析任务的最大等待时间，默认30分钟

## 输出内容

解析完成后，输出的ZIP压缩包包含：
- 文件文本内容提取结果
- 公式识别结果
- 图片提取结果
- 解析元数据信息

## 注意事项

1. 需要有效的MinerU API密钥才能使用(系统内配置)
2. 网络连接必须正常，能够访问MinerU服务
3. 大文件解析可能需要较长时间，请适当调整timeout参数
4. 支持的文件大小受MinerU服务限制
5. 输出目录不存在时会自动创建
