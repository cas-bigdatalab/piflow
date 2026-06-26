---
name: stacked_symbol_cleaner
description: '堆叠符号清洗工具。去除纯符号装饰行/分隔线（====、****、----、~~~~、* * * * *、

  -=-=-=- 等），适配论坛帖子、邮件、旧文档中的符号分隔线清理。当用户提到装饰符号行、

  分隔线清除、符号堆叠等需求时使用此skill。

  '
name_zh: 堆叠符号清洗算子
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
- name: min_repeat
  type: string
  required: false
  default: "4"
  description: 最小连续重复次数
output_params:
- name: output_path
  type: csv_file
  description: 清洗后的结构化数据文件
tag: 清洗
---

# stacked_symbol_cleaner 堆叠符号清洗Skill

## 功能概述

识别并删除纯符号组成的装饰行，支持 3 种模式：(1) 连续重复符号 `====`、`****`、`----`；(2) 带空格符号 `* * * * *`、`- - - -`；(3) 交替符号 `-=-=-=-`、`_._._._`。阈值 `--min_repeat` 控制最小重复次数。

## 触发条件

- 堆叠符号 / 装饰符号行清除
- 分隔线清除 / 符号分隔符
- 论坛/邮件文本清洗
- 旧文本文档清理

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 CSV/TSV/Excel 等结构化文件路径 |
| `--output_path` | 输出清洗后文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 需要处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |
| `--min_repeat` | 判定为堆叠符号装饰行的最小重复次数 | `4` |

## 输入文件格式

输入为结构化表格，文本列可包含纯符号分隔线或装饰行：

```csv
id,text
1,"Title\n====\nBody"
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/stacked_symbol_cleaner.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--min_repeat 4]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--min_repeat` | 否 | 最小重复次数（默认4） |

## 输出示例

```
[OK] 堆叠符号清洗完成 -> output.csv
   文本列: ['text'], min_repeat=4
```

`==========` 和 `* * * * *` 行 → 已删除

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. 只删除整行仅含装饰符号的行，不处理行内符号
2. `min_repeat=4` 时 `---`（3个）保留，`----`（4个）删除
3. 交替模式支持奇数长度（末尾允许多余一个符号1）
