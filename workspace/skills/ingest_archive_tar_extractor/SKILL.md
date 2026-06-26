---
name: ingest_archive_tar_extractor
name_zh: TAR 压缩包解压
description: 'TAR 压缩包解压工具。递归扫描目录内 .tar / .tar.gz / .tar.bz2 / .tar.xz 文件，解压并输出解压清单。不负责
  zip、7z、rar 等其他格式的解压。

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

# ingest_archive_tar_extractor — TAR 压缩包解压

## 功能概述

递归扫描目录内 `.tar`、`.tar.gz`、`.tgz`、`.tar.bz2`、`.tbz2`、`.tar.xz`、`.txz` 文件，解压并输出解压清单。使用 Python 标准库 `tarfile`。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--input_dir` | 是 |  | 待解压目录（递归） |
| `--output_dir` | 是 |  | 解压输出根目录 |
| `--report` | 是 |  | 解压报告输出路径（JSON） |
| `--max_entries` | 否 | 0 | 单包最大解压文件数（0 不限） |

## 使用方法

```bash
python scripts/run_ingest_archive_tar_extractor.py \
  --input_dir <input_dir> \
  --output_dir <output_dir> \
  --report <report.json>
```

## 支持的 TAR 变体

| 扩展名 | 模式 |
|--------|------|
| `.tar` | 无压缩 |
| `.tar.gz` / `.tgz` | gzip |
| `.tar.bz2` / `.tbz2` | bzip2 |
| `.tar.xz` / `.txz` | xz / lzma |
