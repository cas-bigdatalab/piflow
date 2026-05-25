---
name: bdbe_cellanno
description: 本skill是用于单细胞测序数据分析的专用技能，首先需要用户上传需要处理的单细胞测序数据，再对经过预处理的单细胞表达数据进行自动化细胞类型注释。它通过基因比对、数据标准化、降维等一系列流程，将细胞聚类结果与已知参考数据库进行匹配，从而为每个细胞分配生物学功能标签。
compatibility:
  - python
  - requests

name_zh: 单细胞测序细胞类型注释算子
input_params:
  - name: input_file
    type: string
    required: true
    description: 输入单细胞测序数据文件路径（h5ad格式）

  - name: species
    type: string
    required: true
    description: 物种类型，如 mouse、human 等

  - name: output_dir
    type: string
    required: false
    description: 输出目录，默认在上传文件所在目录

output_params:
  - name: output_dir
    type: json_file
    description: 细胞类型注释结果JSON，包含每个细胞的类型标签及分布统计

tag: 其他

---


## Trigger

当用户希望"对单细胞数据进行自动化细胞类型注释"、”使用单细胞数据注释工具“等情况时触发。

## Parameters

| 参数名 | 类型 | 说明 | 示例值 | 是否必填 |
| :--- | :--- | :--- | :--- | :--- |
| input_file | string | 输入单细胞测序数据文件路径 | D:\hqr\workspace\Agent\source\mouse_ERX2609603 | 是 |
| species | string | 物种类型 | mouse | 是 |
| output_dir | string | 输出目录，默认在上传文件所在目录 | D:\hqr\workspace\Agent\output | 否 |

## Examples

### Example 1: 基本使用

```bash
python scripts/bdbe_cellanno.py --input_file "D:\hqr\workspace\Agent\source\mouse_ERX2609603" --species mouse
```

### Example 2: 指定输出目录

```bash
python scripts/bdbe_cellanno.py --input_file "D:\hqr\workspace\Agent\source\mouse_ERX2609603" --species mouse --output_dir "D:\hqr\workspace\Agent\output"
```

## Implementation

### 核心流程

1. **文件上传** - 上传待注释的单细胞数据集文件，获取文件唯一标识ID
2. **启动分析** - 触发细胞类型注释分析，获取分析任务ID
3. **获取结果** - 轮询获取分析结果，直至返回有效结果
4. **下载文件** - 下载生成的细胞类型注释结果文件

### 接口说明

- **文件上传接口**：`https://www.bdbe.cn/kun/api/upload` (POST)
- **分析触发接口**：`https://www.bdbe.cn/kun/api/analysis?tool=CellAnno&id={file_id}&species={species}` (GET)
- **结果获取接口**：`https://www.bdbe.cn/kun/api/result?id={task_id}` (GET)
- **文件下载接口**：`https://www.bdbe.cn/kun/api/result/download?link={link}` (GET)

## Notes

- 支持的文件格式：h5ad格式
- 分析过程可能需要较长时间，脚本会自动轮询等待结果
- 结果包含细胞类型注释列表和CSV格式的结果文件
- 下载的结果文件默认保存在上传文件所在目录，也可通过output_dir参数指定