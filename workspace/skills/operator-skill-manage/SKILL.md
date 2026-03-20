---
name: "operator-skill-manage"
description: "管理算子仓库中的skills，包括查询所有可用skill信息和下载指定skill到指定目录并解压缩。当用户需要查看skill信息或下载skill时调用。"
---

# Operator Skill Manager

## 功能说明

该skill提供从算子仓库服务中管理Skills的能力，包括：

1. **查询所有可用skill信息**：从算子仓库服务获取所有Skill算子信息（名称、版本号、功能描述、地址），并格式化输出，最后给用户提示可以通过输入算子名称和版本号来下载指定的算子。
2. **下载指定skill**：根据skill名称和版本号，从算子仓库服务下载对应的压缩包文件，并解压缩至指定目录。

## 核心功能

### 1. 查询Skills算子信息

通过执行 `skill-operator-list.py` 脚本，从算子仓库服务（http://10.0.89.39:8090）获取Skill算子信息，并智能格式化输出。支持全量查询和分页查询。

**调用方式**：

1. **全量查询**（默认）：
```bash
python scripts/skill-operator-list.py
```

2. **分页查询**：
```bash
python scripts/skill-operator-list.py --page_num <页码> --page_size <每页大小>
```

**参数说明**：
- `--page_num`：可选，页码，从1开始
- `--page_size`：可选，每页显示的算子数量

**输出示例**：

**全量查询输出**：
```
================================================================================
当前算子仓库算子列表
================================================================================

1. 算子名称: alphanumeric_filter
   版本号: 0.1.0
   功能描述: 分析文本中字母 / 数字占比，识别异常字符分布的样本
   Nexus地址: http://10.0.82.112:8081/repository/maven-releases/cn/cnic/alphanumeric_filter/0.1.0/alphanumeric_filter-0.1.0.zip

2. 算子名称: bdbe_cellanno
   版本号: 0.1.0
   功能描述: 本skill隶属可信数据空间，用于单细胞测序数据分析的专用技能
   Nexus地址: http://10.0.82.112:8081/repository/maven-releases/cn/cnic/bdbe_cellanno/0.1.0/bdbe_cellanno-0.1.0.zip

================================================================================
算子列表获取完成,总计 35 个算子
当前页显示 35 个算子
```

**分页查询输出**：
```
[开始] 调用算子列表接口:http://10.0.89.39:8090/api/operators/listAllSkills
[参数] pageNum=1, pageSize=5

================================================================================
当前算子仓库算子列表
================================================================================

1. 算子名称: alphanumeric_filter
   版本号: 0.1.0
   功能描述: 分析文本中字母 / 数字占比，识别异常字符分布的样本
   Nexus地址: http://10.0.82.112:8081/repository/maven-releases/cn/cnic/alphanumeric_filter/0.1.0/alphanumeric_filter-0.1.0.zip

2. 算子名称: bdbe_cellanno
   版本号: 0.1.0
   功能描述: 本skill隶属可信数据空间，用于单细胞测序数据分析的专用技能
   Nexus地址: http://10.0.82.112:8081/repository/maven-releases/cn/cnic/bdbe_cellanno/0.1.0/bdbe_cellanno-0.1.0.zip

================================================================================
算子列表获取完成,总计 35 个算子
当前页显示 5 个算子
```

**补充说明**：
- 用户查询完算子信息后，需要提示用户可以通过输入算子名称和版本号来下载指定的算子。方便用户根据需要选择下载。
- 在展示所有的算子信息时要进行功能分类，例如根据算子的功能描述进行分类，将相似功能的算子放在一起展示。并且优化输出格式，例如使用表格展示算子信息，使信息更易读。
- 当查询到的算子信息过多过长时，返回的查询信息会超过可展示范围，此时需要将查询得到的结果输出到临时文本中，再读取这个文本文件展示给用户，以此保证用户能够完整查看所有算子信息。
- 分页查询功能可以帮助用户更高效地浏览大量算子信息，特别是当算子数量较多时。

### 2. 下载Skill算子

通过执行 `skill-operator-downloader.py` 脚本，根据指定的算子名称、版本号和输出路径，从算子仓库服务下载对应的Skill算子压缩包，并自动解压缩。

**调用方式**：
```bash
python scripts/skill-operator-downloader.py <name> <version> <output_path>
```

**参数说明**：
- `<name>`：必填，算子唯一标识名称，例如 `random-selector`
- `<version>`：必填，算子版本号，例如 `0.0.5`
- `<output_path>`：必填，算子压缩包本地输出路径，支持目录路径或完整文件路径

**使用示例**：
```bash
# 下载到目录
python scripts/skill-operator-downloader.py random-selector 0.0.5 D:\project\skills

# 下载到指定文件
python scripts/skill-operator-downloader.py random-selector 0.0.5 D:\project\skills\random-selector-0.0.5.zip
```

## 脚本说明

### skill-operator-list.py
- **功能**：查询算子仓库中skill的基本信息，支持全量查询和分页查询
- **调用接口**：`http://10.0.89.39:8090/api/operators/listAllSkills`
- **参数**：
  - `--page_num`：可选，页码，从1开始
  - `--page_size`：可选，每页显示的算子数量
- **输出**：格式化的skill信息列表，包含总计算子数量和当前页显示数量

### skill-operator-downloader.py
- **功能**：下载指定skill并解压缩
- **调用接口**：`http://10.0.89.39:8090/api/operators/downloadSkillStream`
- **特性**：
  - 支持流式下载大文件
  - 自动处理目录路径，生成默认文件名
  - 自动解压缩zip文件
  - 智能处理权限和文件占用问题

## 注意事项

1. 确保网络连接正常，能够访问算子仓库服务
2. 下载路径需要有写入权限
3. 脚本在用户本地执行，依赖Python环境
4. 支持Windows和Linux系统

## 依赖

- Python 3.x
- requests 库
- zipfile 库（标准库）
- os, sys, shutil, gc 库（标准库）