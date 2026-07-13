---
name: openBabel_skill
description: |
  分子格式转换工具。支持在 .smi、.mol、.xyz、.gjf、.sdf 等格式之间转换，并可从 SMILES 或 2D 结构生成带坐标的 3D 结构。
  当用户提到分子格式转换、3D构象生成、openbabel等需求时使用此skill。

name_zh: 分子格式转换算子
version: 1.0.0
input_params:
  - name: inputPath
    type: string
    required: true
    description: 输入文件完整路径，例如 /work/jobs/acetic/acetic.smi

  - name: outType
    type: string
    required: true
    description: 输出格式，例如 xyz、mol、gjf、sdf

  - name: isGen3d
    type: bool
    required: true
    description: 是否生成3D构象

  - name: outputDir
    type: string
    required: true
    description: 本次任务输出的工作目录

  - name: primaryOutputPath
    type: string
    required: true
    description: 主输出文件完整路径

  - name: compressedOutputPath
    type: string
    required: true
    description: 其他输出文件压缩包完整路径

output_params:
  - name: outputDir
    type: string
    description: 本次运行目录

  - name: primaryOutputPath
    type: string
    description: 主输出文件

  - name: compressedOutputPath
    type: string
    description: 其他输出文件压缩包路径

tag: 数据转换
disciplinary_field: 化工
---

## 功能概述

该算子基于 OpenBabel 实现分子格式转换和3D构象生成功能。支持多种化学分子文件格式之间的相互转换，并可从 SMILES 或 2D 结构生成带三维坐标的3D结构。

## 核心功能

- **格式转换**: 在 .smi、.mol、.xyz、.gjf、.sdf 等格式之间转换
- **3D构象生成**: 从 SMILES 或 2D 结构生成带坐标的 3D 结构

## 支持的文件格式

输入格式：`.smi`, `.mol`, `.xyz`, `.gjf`, `.sdf` 等 OpenBabel 支持的所有格式

输出格式：`.xyz`, `.mol`, `.gjf`, `.sdf` 等 OpenBabel 支持的所有格式

## 使用示例

### 命令行调用

```bash
# 普通格式转换：smi转xyz
python scripts/run_openBabel_skill.py \
  --inputPath /path/to/acetic.smi \
  --outType xyz \
  --isGen3d false \
  --outputDir /path/to/output \
  --primaryOutputPath /path/to/output/acetic.xyz \
  --compressedOutputPath /path/to/output/output.zip

# 生成3D构象：smi转xyz
python scripts/run_openBabel_skill.py \
  --inputPath /path/to/acetic.smi \
  --outType xyz \
  --isGen3d true \
  --outputDir /path/to/output \
  --primaryOutputPath /path/to/output/acetic.xyz \
  --compressedOutputPath /path/to/output/output.zip

# mol转gjf格式
python scripts/run_openBabel_skill.py \
  --inputPath /path/to/molecule.mol \
  --outType gjf \
  --isGen3d false \
  --outputDir /path/to/output \
  --primaryOutputPath /path/to/output/molecule.gjf \
  --compressedOutputPath /path/to/output/output.zip

# xyz转sdf格式并生成3D
python scripts/run_openBabel_skill.py \
  --inputPath /path/to/molecule.xyz \
  --outType sdf \
  --isGen3d true \
  --outputDir /path/to/output \
  --primaryOutputPath /path/to/output/molecule.sdf \
  --compressedOutputPath /path/to/output/output.zip
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| inputPath | string | 是 | - | 输入文件完整路径，例如 /work/jobs/acetic/acetic.smi |
| outType | string | 是 | - | 输出格式，例如 xyz、mol、gjf、sdf |
| isGen3d | bool | 是 | - | 是否生成3D构象 |
| outputDir | string | 是 | - | 本次任务输出的工作目录 |
| primaryOutputPath | string | 是 | - | 主输出文件完整路径 |
| compressedOutputPath | string | 是 | - | 其他输出文件压缩包完整路径 |

## 输出说明

### 输出文件结构

```
outputDir/
├── <filename>.<outType>    # 主输出文件（转换后的分子文件）
├── stdout.txt              # 标准输出日志
├── stderr.txt              # 标准错误日志
├── openbabel.log           # 主日志文件
├── summary.md              # 任务摘要markdown文件
└── openbabel_output.zip    # 所有输出文件的压缩包
```

### 输出参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| outputDir | string | 本次运行目录 |
| primaryOutputPath | string | 主输出文件路径 |
| compressedOutputPath | string | 其他输出文件压缩包路径 |

## summary.md 内容格式

summary.md 文件包含以下信息：

- **任务状态**: 任务执行状态和输出目录
- **生成文件列表**: 包含所有生成文件的路径、类型和大小
- **结构化摘要**: 输入文件、输出格式、是否生成3D等信息
- **日志路径**: 主日志、stdout、stderr的路径
- **错误信息**: 如果任务失败，包含人类可读的错误原因

## 注意事项

1. 需要在系统中安装 OpenBabel 组件
2. 脚本会自动尝试 `obabel` 和 `openbabel.obabel` 两种命令
3. 输出目录不存在时会自动创建
4. 主输出文件名称与输入文件一致，仅扩展名变更
5. 所有中文内容按 UTF-8 处理
6. 当 isGen3d 为 true 时，会添加 `--gen3d -best` 参数进行3D构象生成