---
name: bdbe_homo
description: 根据多维度筛选条件检索单细胞测序相关的预训练数据集，支持分页查询，返回符合条件的数据集详情，并格式化展示查询结果。
compatibility:
  - python
  - requests

input_params:
  - name: organism
    type: string
    required: true
    description: 生物物种（必填参数）

  - name: organ
    type: string
    required: false
    description: 组织/器官

  - name: class
    type: string
    required: false
    description: 分类

  - name: time
    type: string
    required: false
    description: 发育/采样时间

  - name: gender
    type: string
    required: false
    description: 性别

  - name: cell_line
    type: string
    required: false
    description: 细胞系

  - name: organoid
    type: string
    required: false
    description: 类器官

  - name: tumor
    type: string
    required: false
    description: 肿瘤相关

  - name: page_num
    type: int
    required: false
    default: 1
    description: 分页页码（从1开始）

  - name: page_size
    type: int
    required: false
    default: 10
    description: 每页返回数据集数量

output_params:
  - name: query_result
    type: json_file
    description: 检索结果JSON，包含数据集列表和总数等信息
tag: 其他
---

# bdbe_homo Skill

## 功能描述
根据多维度筛选条件检索单细胞测序相关的预训练数据集，支持分页查询，返回符合条件的数据集详情，并格式化展示查询结果。

## 核心功能
- 支持多维度筛选条件（生物物种、组织/器官、分类、时间、性别等）
- 支持分页查询
- 格式化展示查询结果
- 处理长结果输出

## 参数说明
- `organism`：生物物种（必填参数）
- `organ`：组织/器官（可选）
- `class`：分类（可选）
- `time`：发育/采样时间（可选）
- `gender`：性别（可选）
- `cell_line`：细胞系（可选）
- `organoid`：类器官（可选）
- `tumor`：肿瘤相关（可选）
- `page_num`：分页页码（从1开始，默认1）
- `page_size`：每页返回数据集数量（默认10）

## 依赖
- requests
- json

## 使用示例

### 基本使用
```bash
python scripts/bdbe_homo.py --organism "Acomys cahirinus"
```

### 带筛选条件
```bash
python scripts/bdbe_homo.py --organism "Acomys cahirinus" --organ "ear" --page_num 1 --page_size 5
```

## 输入输出示例

#### 输入
```bash
python scripts/bdbe_homo.py --organism "Acomys cahirinus"
```

#### 输出
```
查询结果：
总数据集数量: 5

数据集 1:
- ID: 62385
- 唯一标识: KUN00100200008268
- 样本编号: GSM5519177
- 生物物种: Acomys cahirinus
- 分类: organ
- 组织/器官: ear
- 细胞系: not applicable
- 发育/采样时间: Adult
- 性别: not applicable
- 系列编号: GSE182141
- 原始数据量: 8559
- 质控后数据量: 8148
- 注释后数据量: 8148
- 数据文件路径: scope/Mouse/GSM5519177_prepared.h5ad
- 数据授权类型: open access
- 测序平台: 10x

页码: 1, 每页数量: 10
```

## 注意事项
- `organism`参数为必填项
- 所有参数支持模糊/精准匹配，空值表示不筛选该维度
- 如果结果过长，会自动输出到临时文件并读取展示
- 响应状态码为0表示检索成功，非0为异常