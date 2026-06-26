---
name: privacy_token_remover
name_zh: 隐私标识清理算子
description: '隐私标识移除工具。读取结构化文本数据，按用户选择的类别删除或替换邮箱、IPv4 地址、电话号码等文本中的隐私标识。

  当用户提到移除邮箱、清洗 IP、替换电话、从文本里剔除隐私 token 等需求时使用此 skill。

  它只处理文本中的 token 清理，不做字段级遮蔽，也不负责图片脱敏、音频脱敏、结构化字段加密或假数据生成。

  '
tag: 清洗
input_params:
- name: input_path
  type: string
  required: true
  description: 输入文件路径
- name: output_path
  type: string
  required: true
  description: 输出文件路径
- name: text_columns
  type: string
  required: false
  description: 处理的文本列，逗号分隔；默认全部字符串列
- name: remove_email
  type: string
  required: false
  description: 是否移除邮箱，默认关闭
- name: remove_ip
  type: string
  required: false
  description: 是否移除 IPv4 地址，默认关闭
- name: remove_phone
  type: string
  required: false
  description: 是否移除电话号码，默认关闭
- name: replace_token
  type: string
  required: false
  description: 替换占位符；默认空字符串表示直接删除
output_params:
- name: output_path
  type: string
  description: 清理后的结构化数据文件
---

# Privacy Token Remover 隐私标识清理 Skill

## 功能概述

按用户指定类别移除或替换文本中的隐私标识：
- 邮箱地址
- IPv4 地址
- 电话号码

所有类别默认关闭，需要用户显式用开关开启。

## 触发条件

- 需要在结构化文本字段中删除邮箱、IP、电话等隐私标识。
- 需要在发布、共享或训练前对文本 token 做轻量清理。

## 核心参数说明

### 必需参数

- `--input_path`：输入文件路径
- `--output_path`：输出文件路径

### 可选参数

- `--remove_email`：开启邮箱移除
- `--remove_ip`：开启 IPv4 地址移除
- `--remove_phone`：开启电话号码移除
- `--text_columns`：处理的文本列，逗号分隔；默认全部字符串列
- `--replace_token`：替换占位符；默认空字符串表示直接删除

## 输入文件格式

支持 CSV、TSV、XLS、XLSX、SAV 格式的结构化数据。

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为以上支持格式后再使用本 skill。

## 使用方法

```bash
# 只移除邮箱
python scripts/run_privacy_token_remover.py \
  --input_path data.csv \
  --remove_email \
  --output_path cleaned.csv \
  --replace_token "[REMOVED]"

# 同时移除邮箱和IP
python scripts/run_privacy_token_remover.py \
  --input_path data.csv \
  --remove_email --remove_ip \
  --output_path cleaned.csv
```

## 输出示例

输入 `Contact alice@example.com from 192.168.1.10`

使用 `--remove_email --remove_ip --replace_token "[HIDDEN]"` 后输出：

```text
Contact [HIDDEN] from [HIDDEN]
```

## 环境要求

使用项目 Python 环境运行，依赖 pandas 和共享 `data_io` 读写工具。

## 注意事项

- 所有类别默认关闭，用户必须用 `--remove_email/--remove_ip/--remove_phone` 显式开启。
- IP 规则只覆盖 IPv4，不覆盖 IPv6。
- 电话规则覆盖常见连续数字和 3-3/4-4 位分段格式。
- 只处理选中的文本列，其他列保持原样。
