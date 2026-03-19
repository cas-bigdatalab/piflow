---
name: sciencedb_search
description: |
  普通数据集检索技能（非分析场景）。优先调用 process，一次传入多个关键词并聚合 ScienceDB 与 InstDB 结果。
  输出必须逐条包含：数据集名称 + 下载链接（InstDB 为 ftp 地址及凭据）。
allowed-tools: process scidb_search_main instDB_search_main
---

# 普通数据集检索技能（ScienceDB + InstDB）

## 使用范围
- 仅用于“找数据 / 查数据 / 下载数据”等普通检索语义。
- 不是分析/建模/流程编排场景。

## 调用规则
- 默认只调用一次 `process`，并传入多个关键词。
- `keywords` 支持字符串或字符串数组。
- 普通检索一轮内不要再追加调用 `scidb_search_main` / `instDB_search_main`，除非用户明确要求只查某单一来源或要求追加二次检索。
- 关键词必须由模型根据用户语义动态生成，禁止写死固定词表。
- 若用户明确指定单一来源（如“只在 ScienceDB 搜索”），可调用单源工具：
  - `scidb_search_main`
  - `instDB_search_main`

## 输出规则（强制）
- 给用户的每条结果只保留这些字段：`数据集名`、`下载链接`、`关键词`、`描述（精简）`、`文件大小`、`来源`。
- 每条结果都要给出可用下载信息：
  - ScienceDB：`https://china.scidb.cn/download?fileId=...`
  - InstDB：`ftpUrl (username: ..., password: ...)`
- 若工具返回同时包含 ScienceDB 与 InstDB 结果，必须把两个来源都展示给用户，不能在总结时丢掉任一来源。
- 普通检索回复应直接按条目展示工具结果，不要改写成摘要段落。
- 不要输出模态覆盖分析、用途建议、下一步建议等扩展说明。
