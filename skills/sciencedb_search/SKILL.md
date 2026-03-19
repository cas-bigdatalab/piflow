---
name: sciencedb_search
description: 搜索 ScienceDB 公开可下载数据集并返回下载链接。用于泛检索/下载场景，不用于流程输入数据源编排。
allowed-tools:
  - process
---

# sciencedb_search

## 路由边界

- 用户是“做某个分析要哪些输入数据源 / DAG / 算子 / 流程编排”时，不调用本 skill。
- 这类问题应走：算法算子 skill + `synergy_datasource_search.process`。
- 用户是“泛数据集检索、公开下载链接、ScienceDB 下载”时调用本 skill。

## 输出约束

调用 `sciencedb_search.process(keyword, size)` 后，回复中每条结果必须包含：

- `数据集名称`
- `下载链接`

如果写“共 N 个结果”，N 必须等于实际列出的条目数。
