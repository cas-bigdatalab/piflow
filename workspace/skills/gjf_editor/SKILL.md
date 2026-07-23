---
name: gjf_editor
name_zh: Gaussian gjf 文件编辑器
description: 用于编辑或创建 Gaussian 输入文件（.gjf），支持添加 Link 0 指令（%chk、%oldchk、%nprocshared、%mem）、Route 行关键词、电荷和多重度。可对已有 gjf 文件进行参数填充，也可从零创建新的 gjf 文件。
version: 1.0.0
input_params:
  - name: input_path
    type: string
    required: false
    description: 输入 gjf 文件路径，若省略则从零创建新文件
  - name: output_path
    type: string
    required: true
    description: 输出 gjf 文件路径
  - name: chk
    type: string
    required: true
    description: Gaussian 检查点文件名
  - name: oldchk
    type: string
    required: false
    description: 上一步计算的检查点文件名，用于 restart 计算
  - name: nprocshared
    type: int
    required: false
    default: 16
    description: CPU 核数
  - name: mem
    type: string
    required: false
    default: 8GB
    description: 内存设置，如 8GB
  - name: keywords
    type: string
    required: true
    description: Gaussian Route 关键词，可带或不带前导 #p
  - name: charge
    type: int
    required: false
    default: 0
    description: 分子总电荷
  - name: multiplicity
    type: int
    required: false
    default: 1
    description: 自旋多重度
  - name: title
    type: string
    required: false
    default: Acetic acid opt freq
    description: Gaussian 标题行
output_params:
  - name: output_path
    type: file
    description: 生成的 gjf 文件路径
tag: 计算化学
---

# gjf_editor 技能

## 功能说明

该技能用于编辑或创建 Gaussian 输入文件（.gjf），主要功能包括：
- 为 OpenBabel 生成的基础 gjf 文件添加完整的计算参数（Link 0 指令、Route 行、电荷和多重度）
- 支持从零创建新的 gjf 文件（不提供输入文件时）
- 支持添加 `%oldchk` 参数用于 restart 计算

## 触发条件

- 当需要为 Gaussian 计算准备输入文件时使用此技能
- 当需要将简单的坐标文件转换为完整的 Gaussian 输入文件时使用此技能
- 当需要设置 restart 计算参数（%oldchk）时使用此技能

## 核心功能

- 添加 Link 0 指令：%chk、%oldchk、%nprocshared、%mem
- 设置 Route 行关键词
- 设置电荷和多重度
- 保留或自定义标题行
- 从零创建空的 gjf 文件模板

## 使用方法

```bash
python scripts/run_gjf_editor.py --input <输入文件> --output <输出文件> --chk <检查点文件> --keywords <关键词>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 否 | - | 输入 gjf 文件路径，省略则创建新文件 |
| output_path | string | 是 | - | 输出 gjf 文件路径 |
| chk | string | 是 | - | 检查点文件名，如 acetic_opt.chk |
| oldchk | string | 否 | - | 上一步检查点文件名，用于 restart |
| nprocshared | int | 否 | 16 | CPU 核数 |
| mem | string | 否 | 8GB | 内存设置 |
| keywords | string | 是 | - | Route 关键词，如 B3LYP/6-31G(d) |
| charge | int | 否 | 0 | 分子总电荷 |
| multiplicity | int | 否 | 1 | 自旋多重度 |
| title | string | 否 | Acetic acid opt freq | 标题行 |

## 示例

### 示例 1：编辑已有 gjf 文件

```bash
python scripts/run_gjf_editor.py \
  -i acetic_no_param.gjf \
  -o acetic_opt.gjf \
  --chk acetic_opt.chk \
  --keywords "B3LYP/6-31G(d) opt freq" \
  --nprocshared 16 \
  --mem 8GB \
  --charge 0 \
  --multiplicity 1 \
  --title "Acetic acid opt freq"
```

### 示例 2：带 restart 参数的单点能计算

```bash
python scripts/run_gjf_editor.py \
  -i acetic_no_param.gjf \
  -o acetic_sp.gjf \
  --oldchk acetic_opt.chk \
  --chk acetic_sp.chk \
  --keywords "B3LYP/6-31G(d) geom=allcheck guess=read" \
  --nprocshared 16 \
  --mem 8GB
```

### 示例 3：从零创建新文件

```bash
python scripts/run_gjf_editor.py \
  -o new_molecule.gjf \
  --chk new_molecule.chk \
  --keywords "B3LYP/6-31G(d) opt"
```

## 输出格式

生成的 gjf 文件结构：

```
%oldchk=acetic_opt.chk          ← 可选，仅当提供 oldchk 参数时
%chk=acetic_sp.chk
%nprocshared=16
%mem=8GB
#p B3LYP/6-31G(d) geom=allcheck guess=read

Acetic acid opt freq

0 1
[坐标行]                         ← 从输入文件提取或为空
```

## 注意事项

- UTF-8 编码读写
- 输出目录不存在时自动创建
- 若不提供输入文件，生成的 gjf 文件仅包含参数部分，需手动添加坐标