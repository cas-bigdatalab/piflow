---
name: bdbe_scnorm
description: 用于单细胞测序数据预处理的专用技能，对单细胞表达矩阵进行标准化处理，以消除技术偏差，为聚类、差异表达分析提供可靠的数据基础。
compatibility:
  - python
  - requests

name_zh: 单细胞测序数据预处理算子
input_params:
  - name: input_file
    type: string
    required: true
    description: 输入单细胞测序数据文件路径（支持h5ad、csv等格式）

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
    type: h5ad_file
    description: 标准化后的单细胞数据集文件（h5ad格式）

  - name: auxiliary_files
    type: json_file
    description: 辅助文件，包含state.json、dataset_info.json等
tag: 其他

---

# bdbe_scnorm Skill

## 功能描述
本skill是用于单细胞测序数据预处理的专用技能，首先需要用户上传需要处理的单细胞测序数据，再对单细胞表达矩阵进行标准化处理，以消除技术偏差，为聚类、差异表达分析提供可靠的数据基础。

## 核心功能
- 支持上传单细胞测序数据文件
- 触发标准化分析任务
- 获取并展示分析结果
- 支持下载标准化后的数据集

## 参数说明
- `input_file`：输入单细胞测序数据文件路径（必要参数）
- `species`：物种类型（必要参数），如 mouse、human 等

## 依赖
- requests
- json

## 使用示例

### 基本使用
```bash
python scripts/bdbe_scnorm.py --input_file mouse_ERX2557277.csv --species mouse
```

## 输入输出示例

#### 输入
```bash
python scripts/bdbe_scnorm.py --input_file mouse_ERX2557277.csv --species mouse
```

#### 输出
```
正在上传文件: mouse_ERX2557277.csv
上传成功，文件ID: 36885

正在启动标准化分析...
分析任务启动成功，任务ID: 1063

正在获取分析结果...
分析完成，结果文件：

核心文件：
- d5f99079c24ca7b47667bddd59d23621.h5ad
  下载链接: https://www.bdbe.cn/kun/api/result/download?link=-1/python3/mnt/run.py/2026-03-10T10_40_10.091473/output/mouse/d5f99079c24ca7b47667bddd59d23621.h5ad

辅助文件：
- state.json
- dataset_info.json
- sorted_length.pickle
- data-00000-of-00001.arrow
- logs.txt

分析完成！
```

## 注意事项
- 支持的文件格式：h5ad、csv 等常见单细胞数据格式
- 文件大小限制：建议不超过100MB
- 分析时间：根据数据大小，可能需要几分钟到几十分钟
- 物种参数：必须指定正确的物种类型，如 mouse、human 等