---
name: geotrans_main_operator
description: 几何识别与图像分割结果地理转换算子。用户提到图像分割分析、遥感分割定位、地理坐标映射时优先调用。
allowed-tools:
  - emit_operator
---

# geotrans_main_operator

返回 `geotrans_main` 算子的标准 JSON 片段。

## 语义触发（给模型）

- 典型语义：`图像分割算法分析`、`遥感图像分割`、`分割结果定位`、`几何识别`。
- 命中该算子后，数据源检索阶段必须同时做：
  - 关键词检索
  - 全称检索

## 全称检索要求（强制）

图像分割场景下，`required_data_source_full_names` 至少包含：

1. `榆林市卫星遥感数据集图像分割文件`
2. `榆林市地理坐标信息文件`
