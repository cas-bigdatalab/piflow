---
name: ingest_archive_rar_extractor
name_zh: RAR 压缩包解压
description: 'RAR 压缩包解压工具。递归扫描目录内 .rar 文件及分卷（.part1.rar/.part2.rar 等），解压并输出解压清单。依赖
  rarfile 库及系统 unrar 工具。不负责 zip、7z 等其他格式的解压。

  '
input_params:
- name: input_dir
  type: string
  required: true
  description: 待解压目录（递归）
- name: output_dir
  type: string
  required: true
  description: 解压输出根目录
- name: report
  type: string
  required: true
  description: 解压报告输出路径（JSON）
- name: max_entries
  type: string
  required: false
  default: "0"
  description: 单包最大解压文件数（0 不限）
output_params:
- name: output_dir
  type: directory
  description: 解压输出根目录
- name: report
  type: json_file
  description: 解压报告
tag: 采集
---

# ingest_archive_rar_extractor — RAR 压缩包解压

## 功能概述

递归扫描目录内 `.rar` 文件及分卷（`.part1.rar`/`.part2.rar` 等），解压并输出解压清单。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--input_dir` | 是 |  | 待解压目录（递归） |
| `--output_dir` | 是 |  | 解压输出根目录 |
| `--report` | 是 |  | 解压报告输出路径（JSON） |
| `--max_entries` | 否 | 0 | 单包最大解压文件数（0 不限） |

## 使用方法

```bash
python scripts/run_ingest_archive_rar_extractor.py \
  --input_dir <input_dir> \
  --output_dir <output_dir> \
  --report <report.json>
```

## 环境要求

需要 `rarfile` 第三方库及系统安装 unrar 工具。若未安装则报错记录到报告中。
