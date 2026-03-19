---
name: sciencedb_search
description: 搜索 ScienceDB 公开可下载数据集并返回下载链接。用于普通数据集检索/下载场景，不用于分析流程输入编排。
allowed-tools:
  - process
---

# sciencedb_search

## 路由边界

- 当用户问题是“做某个分析需要哪些输入数据源 / DAG / 算子 / 流程编排”时，不调用本 skill。
- 这类问题应走：算法算子 skill + `synergy_datasource_search.process`。
- 当用户是“普通找数据集、查公开下载链接、做 ScienceDB 检索”时，调用本 skill。

## 输出约束（强制）

调用 `sciencedb_search.process(keyword, size)` 后，面向用户回复中每条结果必须包含：

- `数据集名称`
- `下载链接`

并且：

- 禁止只给概括性推荐而省略下载链接。
- 若写“共 N 个结果”，N 必须等于实际列出的条目数。
- 若工具返回可下载条目，则应优先完整转述工具结果中的名称与链接。

