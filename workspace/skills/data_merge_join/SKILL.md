---
name: data_merge_join
description: |
  数据横向关联工具。读取多个结构化数据文件，按指定键进行横向关联（JOIN），输出关联后的合并文件。
  当用户提到数据关联、表连接、横向合并、键合并、JOIN等需求时使用此skill。
  即使用户没有明确说出"关联"，只要任务涉及按某个字段将多个表的数据关联在一起，就应该使用此skill。
  不负责数据纵向拼接（concat）、数据去重、或字段值聚合（GROUP BY）。

name_zh: 数据横向关联算子
input_params:
  - name: input_files
    type: string
    required: true
    description: 输入文件路径列表，多个文件用逗号分隔

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: join_key
    type: string
    required: true
    description: 关联键字段名（必须在所有文件中存在）

  - name: join_how
    type: string
    required: false
    default: inner
    description: 关联方式：inner（内连接）、left（左连接）、right（右连接）、outer（全连接）

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
    description: 关联后的数据文件
tag: 增强

---

# Data Merge Join 数据横向关联 Skill

## 功能概述

本skill用于将多个结构化数据文件按指定键进行横向关联（JOIN），支持内连接（inner）、左连接（left）、右连接（right）、全连接（outer）四种方式。多文件关联时按顺序依次进行两两关联，重名列自动添加后缀 `_1`、`_2` 以避免冲突。

```
文件1:          文件2:          关联结果(inner join on key):
| key | A |     | key | B |     | key | A | B |
|-----|---|     |-----|---|     |-----|---|---|
| k1  | 1 |     | k1  | x |     | k1  | 1 | x |
| k2  | 2 |     | k3  | y |
```

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数据关联/表连接
- 横向合并/键合并
- JOIN操作
- 按字段关联数据

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_files` | 输入文件路径列表，多个文件用逗号分隔 |
| `--output` | 输出文件路径 |
| `--join_key` | 关联键字段名，必须在所有输入文件中存在 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--join_how` | 关联方式：inner/left/right/outer | `inner` |
| `--use_dask` | 是否使用Dask处理大数据 | `False` |
| `--blocksize` | Dask分块大小 | `64MB` |

## 输入文件格式

支持 CSV、TSV、Excel（.xls/.xlsx）、SPSS（.sav）格式的结构化数据文件，每个文件必须包含关联键字段。

**示例 employees.csv：**
```csv
employee_id,name,department_id,salary,city
E001,Alice,SALES,8000,Beijing
E002,Bob,ENG,12000,Shanghai
```

**示例 departments.csv：**
```csv
department_id,dept_name,manager,location
SALES,Sales Department,Alice,Beijing
ENG,Engineering Department,Bob,Shanghai
```

## 使用方法

### 内连接（只保留两表都匹配的行）
```bash
python scripts/run_data_merge_join.py \
  --input_files "file1.csv,file2.csv" \
  --output merged.csv \
  --join_key "id" \
  --join_how inner
```

### 左连接（保留左表所有行）
```bash
python scripts/run_data_merge_join.py \
  --input_files "main.csv,lookup.csv" \
  --output merged.csv \
  --join_key "user_id" \
  --join_how left
```

### 右连接（保留右表所有行）
```bash
python scripts/run_data_merge_join.py \
  --input_files "main.csv,lookup.csv" \
  --output merged.csv \
  --join_key "dept_id" \
  --join_how right
```

### 全连接（保留两表所有行）
```bash
python scripts/run_data_merge_join.py \
  --input_files "table_a.csv,table_b.csv" \
  --output merged.csv \
  --join_key "key" \
  --join_how outer
```

## 输出示例

**命令行输出：**
```
[OK] Data merge completed!
   Engine: pandas
   Merge type: join
   Input files: 2
   Total rows before merge: 10, 5
   Total rows after merge: 8
   Total columns after merge: 8
   Output file: merged.csv
```

**输出CSV格式：**
```csv
employee_id,name,department_id,salary,city,dept_name,manager,location
E001,Alice,SALES,8000,Beijing,Sales Department,Alice,Beijing
E002,Bob,ENG,12000,Shanghai,Engineering Department,Bob,Shanghai
```

## 环境要求

本skill依赖 pandas 及可选依赖 dask、chardet：
```bash
pip install pandas openpyxl xlrd xlwt chardet
# 可选：大数据场景
pip install dask[dataframe]
```

## 注意事项

1. join_key必须在所有输入文件中存在，否则程序会报错
2. 多文件关联时，按顺序依次进行两两关联
3. 重名列会自动添加后缀 `_1`、`_2` 等以避免冲突
4. 不负责纵向拼接堆叠（concat），如需纵向合并请使用其他skill
