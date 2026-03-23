---
name: sciencedb_search
description: >
  普通数据集检索技能（非分析场景）。优先使用 process，一次传入多个关键词，
  合并 ScienceDB 与 InstDB 结果并去重。
allowed-tools: process scidb_search_main instDB_search_main
---

# 普通数据集检索（ScienceDB + InstDB）

## 适用场景
- 仅用于“找数据 / 查数据 / 下载数据”。
- 不用于分析、建模、流程编排、算子执行。

## 调用规则
- 默认只调用一次 `process`。
- `keywords` 可传字符串或字符串数组。
- 关键词由模型根据用户语义动态生成，禁止写死固定词表。
- 同一轮内不要再追加 `scidb_search_main` / `instDB_search_main`，除非用户明确要求只查单一来源或要求继续检索。
- 若 `sources=all` 且两源都有结果，最终展示必须同时包含 ScienceDB 与 InstDB。

## 输出规则（强制）
- 每条结果只保留这些字段：
  - 数据集名
  - 下载链接
  - 关键词
  - 描述（精简）
  - 文件大小
  - 来源
- ScienceDB 结果必须提供可下载链接（`https://china.scidb.cn/download?fileId=...`）。
- InstDB 结果必须提供 FTP 下载信息（`ftpUrl (username: ..., password: ...)`）。
- 面向用户回复时，按条目直出结果，不要改写成总结段落，不要省略“来源”字段。
