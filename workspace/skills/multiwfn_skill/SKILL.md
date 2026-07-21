---
name: multiwfn_skill
description: "使用 Multiwfn 波函数分析程序读取 Gaussian 生成的 .fchk 文件，提取 HOMO/LUMO、原子电荷、分子表面分析等信息。"
name_zh: 波函数分析算子
version: "1.0.0"
tag: "科学计算"
input_params:
  - name: input_path
    type: string
    required: true
    description: "输入文件路径（.fchk, .wfn, .wfx 等）"
  - name: other_param
    type: string
    required: false
    description: "Multiwfn 命令序列（多行字符串）"
  - name: threads
    type: int
    required: false
    description: "计算线程数（默认 32）"
  - name: multiwfn_path
    type: string
    required: false
    description: "Multiwfn 安装路径"
  - name: output_dir
    type: string
    required: true
    description: "输出工作目录(输出文件都生成在此路径下)"
  - name: mout_output_path
    type: string
    required: true
    description: "Multiwfn 主输出日志路径"
  - name: compressed_output_path
    type: string
    required: true
    description: "其他输出文件压缩包路径"
output_params:
  - name: output_dir
    type: string
    description: "输出工作目录(输出文件都生成在此路径下)"
  - name: mout_output_path
    type: string
    description: "Multiwfn 主输出日志路径"
  - name: compressed_output_path
    type: string
    description: "其他输出文件压缩包路径"
disciplinary_field: 化工
---

# Multiwfn Wavefunction Analysis

## 功能说明

使用 Multiwfn 波函数分析程序读取 Gaussian 生成的 .fchk 文件，提取或计算以下信息：

- **HOMO / LUMO / HOMO-LUMO gap** - 轨道能级信息
- **原子电荷、布居分析** - Mulliken、Hirshfeld、ADCH 等电荷模型
- **分子表面分析** - 体积、表面积、极值、平均值、方差
- **表面映射性质** - 静电势、局域电离能、电子附着能等

## 触发条件

当需要对 Gaussian 生成的波函数文件进行详细分析时触发。

## 使用方法

```bash
python scripts/run_multiwfn_skill.py \
    --input_path molecule.fchk \
    --other_param "0\n7\n11\n1\nn\n0\n12\n2\n1\n0\n11\nn\n-1\n2\n2\n0\n11\nn\n-1\n2\n4\n0\n11\nn\n-1\n2\n-4\n0\n11\nn\n-1\n2\n12\n0\n11\nn\n-1\n2\n11\n0\n11\nn\n-1\n-1\n22\n0\nq" \
    --threads 32 \
    --output_dir outputs \
    --mout_output_path outputs/molecule.mout \
    --compressed_output_path outputs/output.zip
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| input_path | string | 是 | 输入文件路径（.fchk, .wfn, .wfx 等） |
| other_param | string | 否 | Multiwfn 命令序列（多行字符串） |
| threads | int | 否 | 计算线程数（默认 32） |
| multiwfn_path | string | 否 | Multiwfn 安装路径 |
| output_dir | string | 是 | 输出工作目录 |
| mout_output_path | string | 是 | Multiwfn 主输出日志路径 |
| compressed_output_path | string | 是 | 其他输出文件压缩包路径 |

## 输出参数

| 参数 | 类型 | 说明 |
|------|------|------|
| mout_output_path | string | Multiwfn 主输出日志路径 |
| compressed_output_path | string | 其他输出文件压缩包路径 |

## 输出结构

输出目录包含：
- `*.mout` - Multiwfn 主输出日志
- `summary.json` - 提取的结构化摘要
- `stderr.log` - 错误日志（如有）
- `output.zip` - 包含 summary.json 和 stderr.log 的压缩包

## summary.json 结构

```json
{
  "tool": "Multiwfn",
  "inputPath": "/path/input.fchk",
  "moutPath": "/path/output.mout",
  "normalExit": true,
  "formula": "H4 C2 O2",
  "atomCount": 8,
  "molecularMass": 60.05204,
  "electronCount": 32.0,
  "numThreads": 32,
  "wavefunctionType": "restricted single-determinant",
  "orbitals": {
    "homo": { "orbitalIndex": 16, "energyAu": -0.271829, "energyEv": -7.396854 },
    "lumo": { "orbitalIndex": 17, "energyAu": 0.009501, "energyEv": 0.258535 },
    "gap": { "energyAu": 0.281330, "energyEv": 7.655389, "energyKjMol": 738.632875 }
  },
  "surfaceAnalyses": [...],
  "populationAnalysis": { "chargeModels": [...] },
  "atomSurfaceContributions": [...]
}
```

## 依赖

- Python 3.x
- Multiwfn 3.8+

## 注意事项

1. 确保已正确安装 Multiwfn 并配置 `MULTIWFN_ROOT` 环境变量
2. `other_param` 参数支持多行字符串，每行一个 Multiwfn 命令
3. 当前仅支持 Linux 环境