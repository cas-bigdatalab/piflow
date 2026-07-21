---
name: gaussian_executor
description: "使用 Gaussian 软件执行量子化学计算，包括 DFT 结构优化、频率分析和单点能计算。生成 .log 和 .chk 文件，并将所有输出打包为 zip 压缩包。"
name_zh: 量子化学计算算子
version: 1.0.0
tag: "科学计算"
input_params:
  - name: input_path
    type: string
    required: true
    description: "输入 .gjf 文件路径"
  - name: output_dir
    type: string
    required: true
    description: "输出工作目录"
  - name: log_output_path
    type: string
    required: true
    description: "log 文件输出路径"
  - name: chk_output_path
    type: string
    required: true
    description: "chk 文件输出路径"
  - name: compressed_output_path
    type: string
    required: true
    description: "输出文件压缩包路径"
  - name: other_param
    type: string
    required: false
    default: ""
    description: "额外参数"
output_params:
  - name: output_dir
    type: string
    description: "输出工作目录"
  - name: log_output_path
    type: string
    description: "log 文件输出路径"
  - name: chk_output_path
    type: string
    description: "chk 文件输出路径"
  - name: compressed_output_path
    type: string
    description: "输出文件压缩包路径"
disciplinary_field: 化工
---

# Gaussian Executor 技能

## 功能说明

使用 Gaussian 软件执行量子化学计算，包括 DFT 结构优化、频率分析和单点能计算。生成 .log 和 .chk 文件，并将所有输出打包为 zip 压缩包。

## 触发条件

- DAG 类型：量子化学计算

## 核心功能

- DFT 结构优化和频率分析
- DFT 单点能计算
- 生成 .log 和 .chk 文件
- 打包输出文件为 zip 压缩包
- 兼容 Windows 和 Linux 系统
- 自动检测环境变量，未设置时使用默认值

## 使用方法

```bash
python scripts/run_gaussian_executor.py --input_path <input_path> --output_dir <output_dir> --log_output_path <log_output_path> --chk_output_path <chk_output_path> --compressed_output_path <compressed_output_path> [--other_param <other_param>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入 .gjf 文件路径 |
| output_dir | string | 是 | - | 输出工作目录 |
| log_output_path | string | 是 | - | log 文件输出路径 |
| chk_output_path | string | 是 | - | chk 文件输出路径 |
| compressed_output_path | string | 是 | - | 输出文件压缩包路径 |
| other_param | string | 否 |  | 额外参数 |

## 输出参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| log_output_path | string | - | log 文件输出路径 |
| chk_output_path | string | - | chk 文件输出路径 |
| compressed_output_path | string | - | 输出文件压缩包路径 |

## 示例

### 基本调用

```bash
python scripts/run_gaussian_executor.py --input_path input.gjf --output_dir outputs --log_output_path outputs/output.log --chk_output_path outputs/output.chk --compressed_output_path outputs/output.zip
```

## 依赖

- Python 3.x
- Gaussian 16

## 注意事项

- 所有中文内容按 UTF-8 处理。
- 调用脚本时只传入用户明确提供或有默认值的参数。
- 输出文件路径应写入 PiFlow 工作区可访问的位置。
