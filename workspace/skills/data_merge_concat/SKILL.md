---
name: data_merge_concat
description: |
  数据纵向拼接工具。读取多个具有相同列结构的结构化数据文件，执行按行纵向追加合并（concat），输出单一合并文件。
  当用户提到数据拼接、纵向合并、行合并、数据追加、文件合并等需求时使用此skill。
  即使用户没有明确说出"拼接"，只要任务涉及将多个同构数据文件上下合并为一个，就应该使用此skill。
  不负责横向关联（join/merge on key）、字段级合并或非结构化文档聚合。如需按键值关联请使用其他skill。

name_zh: 数据纵向拼接算子
input_params:
  - name: input_files
    type: string
    required: true
    description: 输入文件路径列表，多个文件用逗号分隔

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: ignore_index
    type: string
    required: false
    default: "True"
    description: 是否忽略原索引重新编号

  - name: use_dask
    type: string
    required: false
    default: "False"
    description: 是否使用Dask处理大数据

  - name: blocksize
    type: string
    required: false
    default: "64MB"
    description: Dask分块大小

output_params:
  - name: output
    type: csv_file
    description: 拼接后的数据文件
tag: 增强

---

# Data Merge Concat 数据纵向拼接 Skill

## 功能概述

本skill用于将多个具有相同列结构的数据文件纵向拼接（按行合并）。

```
文件1:          文件2:          合并结果:
| A | B |       | A | B |       | A | B |
|---|---|----       |---|---|       |---|---|
| 1 | 2 |       | 5 | 6 |       | 1 | 2 |
| 3 | 4 |       | 7 | 8 |       | 3 | 4 |
                                | 5 | 6 |
                                | 7 | 8 |
```

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数据拼接/纵向合并
- 行合并/数据追加
- 多文件上下合并

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_files` | 输入文件路径，多个文件用逗号分隔 |
| `--output` | 输出文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--ignore_index` | 是否忽略原索引重新编号 | `True` |
| `--use_dask` | 是否使用Dask处理大数据 | `False` |
| `--blocksize` | Dask分块大小 | `64MB` |

## 输入文件格式

所有输入文件必须具有相同的列结构（列名和列数一致）。支持的格式：

- **CSV** (`.csv`)：逗号分隔值
- **TSV** (`.tsv`)：制表符分隔值
- **Excel** (`.xls`, `.xlsx`)：电子表格
- **SPSS** (`.sav`)：SPSS 数据文件

示例输入结构（file1.csv）：
```csv
experiment,treatment,value,baseline,remark
A,control,10,100,normal
A,control,11,101,normal
```

## 使用方法

### 基本用法（纵向拼接多个CSV文件）
```bash
python scripts/run_data_merge_concat.py \
  --input_files "file1.csv,file2.csv,file3.csv" \
  --output merged.csv
```

### 保留原索引
```bash
python scripts/run_data_merge_concat.py \
  --input_files "file1.csv,file2.csv" \
  --output merged.csv \
  --ignore_index False
```

### 使用Dask处理大数据
```bash
python scripts/run_data_merge_concat.py \
  --input_files "large1.csv,large2.csv" \
  --output merged.csv \
  --use_dask True \
  --blocksize "128MB"
```

## 输出示例

**命令行输出：**
```
[OK] Data merge completed!
   Engine: pandas
   Merge type: concat
   Input files: 3
   Total rows before merge: 4, 2, 6
   Total rows after merge: 12
   Total columns after merge: 5
   Output file: merged.csv
```

**输出CSV格式：**
```csv
experiment,treatment,value,baseline,remark
A,control,10,100,normal
A,control,11,101,normal
A,treat,12,120,normal
B,control,20,200,normal
B,treat,100,500,outlier
```

## 环境要求

本skill使用标准Python数据科学库：
```bash
pip install pandas openpyxl xlrd xlwt
```

可选依赖（大文件Dask模式）：
```bash
pip install dask[dataframe]
```

## 注意事项

1. 所有输入文件必须具有相同的列结构和列数
2. 输出文件格式由输出路径的扩展名决定
3. 大文件合并建议开启Dask模式（`--use_dask True`）
4. 混合编码文件（UTF-8/GBK）会自动检测编码
