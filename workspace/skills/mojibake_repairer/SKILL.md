---
name: mojibake_repairer
description: |
  乱码修复工具。自动检测并修复因编码错误解释导致的乱码文本（Mojibake），支持 GBK/UTF-8、Latin-1/UTF-8、
  Big5、Shift_JIS 等 11 种编码链自动尝试，通过字符合理度评分自动选择最佳修复结果。
  当用户提到乱码修复、编码修复、mojibake、文字乱码、编码错误等需求时使用此skill。
name_zh: 乱码修复算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔
  - name: min_score
    type: string
    required: false
    default: "0.6"
    description: 最小修复评分阈值(0-1)
  - name: chain
    type: string
    required: false
    description: 手动指定编码修复链，如 gbk:utf-8
output_params:
  - name: output_path
    type: csv_file
    description: 乱码修复后的结构化数据文件
tag: 清洗
---

# mojibake_repairer 乱码修复Skill

## 功能概述

自动检测文本中的编码乱码（Mojibake），尝试 11 种编码修复链（gbk→utf-8、latin-1→utf-8、shift_jis→utf-8 等），通过字符合理度评分选择最佳结果。支持中、日、韩、西文等多语言乱码场景。

## 触发条件

- 乱码修复 / 编码修复
- Mojibake 检测
- 编码错误纠正
- 文字乱码处理
- 数据库导出编码错乱

## 核心参数说明

### 必需参数

| 参数 | 说明 |
|------|------|
| `--input_path` | 输入文件路径 |
| `--output_path` | 输出文件路径 |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |
| `--min_score` | 最小修复评分阈值(0-1) | 0.6 |
| `--chain` | 手动指定编码修复链，如 gbk:utf-8 | 自动检测 |

## 输入文件格式

输入为结构化表格，至少包含一个可疑乱码文本列：

```csv
id,text
1,"FranÃ§ois visited SÃ£o Paulo for cafÃ© research."
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/mojibake_repairer.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--min_score 0.6] \
    [--chain gbk:utf-8]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--min_score` | 否 | 最小修复评分（默认0.6） |
| `--chain` | 否 | 手动指定编码链 |

## 输出示例

```
[REPAIR] 共修复 3 处乱码:
  [text][行0] gbk→utf-8 (score=1.00)
    娴嬭瘯鏁版嵁 → 测试数据
  [text][行1] latin-1→utf-8 (score=1.00)
    cafÃ© rÃ©sumÃ© → café résumé
[OK] 乱码修复完成 -> output.csv  (模式=自动检测, min_score=0.6)
```

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. 自动模式尝试 src_encoding→utf-8 方向，避免反向链的误报
2. 编码失败产物（? 和 �）超过 15% 的修复结果会被拒绝
3. 原始文本评分已经很高时（如正常 CJK 文本），不会误触发修复
4. 可通过 `--chain` 手动指定编码链覆盖自动检测
