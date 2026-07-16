---
name: gaussian_chk_to_fchk
description: "使用 Gaussian 的 formchk 工具将 chk 检查点文件转换为 fchk 波函数文本文件。"
name_zh: Gaussian检查点转换算子
version: "1.0.0"
tag: "科学计算"
input_params:
  - name: input_path
    type: string
    required: true
    description: "输入 chk 文件路径"
  - name: other_param
    type: string
    required: false
    description: "额外参数"
  - name: fchk_output_path
    type: string
    required: true
    description: "转换后的 fchk 文件路径"
  - name: compressed_output_path
    type: string
    required: true
    description: "输出文件压缩包路径"
output_params:
  - name: fchk_output_path
    type: string
    description: "转换后的 fchk 文件路径"
  - name: compressed_output_path
    type: string
    description: "输出文件压缩包路径"
disciplinary_field: 化工
---

# Gaussian chk to fchk Converter

## 功能说明

使用 Gaussian 的 `formchk` 工具将 chk 检查点文件转换为 fchk 波函数文本文件。支持 Windows 和 Linux 系统。

## 触发条件

当需要将 Gaussian 计算生成的 chk 文件转换为 fchk 文本格式时触发。

## 使用方法

```bash
python scripts/run_gaussian_chk_to_fchk.py \
    --input_path input.chk \
    --fchk_output_path output.fchk \
    --compressed_output_path output.zip
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| input_path | string | 是 | 输入 chk 文件路径 |
| other_param | string | 否 | 额外参数 |
| fchk_output_path | string | 是 | 转换后的 fchk 文件路径 |
| compressed_output_path | string | 是 | 输出文件压缩包路径 |

## 输出参数

| 参数 | 类型 | 说明 |
|------|------|------|
| fchk_output_path | string | 转换后的 fchk 文件路径 |
| compressed_output_path | string | 输出文件压缩包路径 |

## 输出结构

输出目录包含：
- `*.fchk` - 转换后的波函数文本文件
- `stderr.log` - 错误日志（如有）
- `output.zip` - 包含所有输出文件的压缩包

## 依赖

- Python 3.x
- Gaussian 16

## 注意事项

1. 确保已正确安装 Gaussian 并配置环境变量
2. 在 Linux 上，环境变量会自动从 `~/.bashrc` 中读取
3. 在 Windows 上，需要设置 `g16root` 环境变量或确保 Gaussian 安装在默认路径