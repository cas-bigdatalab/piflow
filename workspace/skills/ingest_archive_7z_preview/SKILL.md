---
name: ingest_archive_7z_preview
description: '7z 压缩包内容预览工具。递归扫描目录内 .7z 文件，列出内部文件清单并按需输出文本片段预览，供后续采集流程判断是否需要解压处理。

  当用户提到 7z 预览、7z 压缩包内容查看、7z 文件清单等需求时使用此 skill。

  即使用户没有明确说出"7z 预览"，只要任务涉及在解压前先查看 7z 压缩包内部文件结构和内容片段，就应该使用此 skill。

  不负责 zip、rar、tar 等其他压缩格式的预览（各有独立 skill），也不负责解压或归档打包。

  '
name_zh: 7z 压缩包预览
input_params:
- name: input_dir
  type: string
  required: true
  description: 待扫描目录（递归）
- name: output
  type: string
  required: true
  description: 预览报告输出路径（JSON）
- name: max_entries
  type: string
  required: false
  default: "0"
  description: 每个压缩包最多列出的文件数，0 表示不限
- name: preview_bytes
  type: string
  required: false
  default: "200"
  description: 文本文件预览字节数
output_params:
- name: output
  type: json_file
  description: 7z 压缩包预览报告
tag: 采集
---

# ingest_archive_7z_preview — 7z 压缩包预览

## 功能概述

递归扫描目录内 `.7z` 文件，列出每个压缩包内部文件清单，对文本文件输出前 N 字节预览（UTF-8 解码失败则输出 hex）。输出 JSON 报告供后续解压或采集流程决策。

依赖 `py7zr` 库。

## 触发条件

- 采集入口收到一批 7z 文件，需要先查看内容再决定解压策略
- 需要批量盘点 7z 压缩包内的文件结构

## 核心参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input_dir` | 待扫描目录（递归） | 必填 |
| `--output` | 预览报告输出路径 | 必填 |
| `--max_entries` | 每个压缩包最多列出的文件数 | 0 |
| `--preview_bytes` | 文本文件预览字节数 | 200 |

## 使用方法

```bash
python scripts/run_ingest_archive_7z_preview.py \
  --input_dir <input_dir> \
  --output <output> \
  --max_entries 0 \
  --preview_bytes 200
```

## 输出示例

```json
{
  "items": [
    {
      "path": "data/batch01.7z",
      "type": "7z",
      "total_entries": 5,
      "entries": [
        {"name": "data.csv", "size": 1024, "is_dir": false, "preview": "id,name,value..."},
        {"name": "docs/", "size": 0, "is_dir": true}
      ]
    }
  ],
  "summary": {"total_archives": 1, "errors": 0}
}
```

## 环境要求

需要 `py7zr` 第三方库。若未安装，报告中将输出 error 提示。
