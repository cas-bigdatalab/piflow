# Skill: bdbe_sexdetermine

## Overview

本skill是用于单细胞样本性别判定的专用技能，首先需要用户上传需要处理的单细胞样本数据，再判定未标注性别的样本，或纠正标注错误的性别信息，生成最后的修正文件。

## Trigger

当用户希望"对单细胞样本进行性别判定"、”使用单细胞样本性别判定工具“等情况时触发。

## Parameters

| 参数名 | 类型 | 说明 | 示例值 | 是否必填 |
| :--- | :--- | :--- | :--- | :--- |
| input_file | string | 输入单细胞样本数据文件路径 | D:\hqr\workspace\Agent\source\mousedemo.csv | 是 |
| species | string | 物种类型 | mouse | 是 |
| output_dir | string | 输出目录，默认在上传文件所在目录 | D:\hqr\workspace\Agent\output | 否 |

## Examples

### Example 1: 基本使用

```bash
python scripts/bdbe_sexdetermine.py --input_file "D:\hqr\workspace\Agent\source\mousedemo.csv" --species mouse
```

### Example 2: 指定输出目录

```bash
python scripts/bdbe_sexdetermine.py --input_file "D:\hqr\workspace\Agent\source\mousedemo.csv" --species mouse --output_dir "D:\hqr\workspace\Agent\output"
```

## Implementation

### 核心流程

1. **文件上传** - 上传待判定性别的单细胞样本文件，获取文件唯一标识ID
2. **启动分析** - 触发性别判定分析，获取分析任务ID
3. **获取结果** - 轮询获取分析结果，直至返回有效结果
4. **下载文件** - 下载生成的性别判定结果文件

### 接口说明

- **文件上传接口**：`https://www.bdbe.cn/kun/api/upload` (POST)
- **分析触发接口**：`https://www.bdbe.cn/kun/api/analysis?tool=SexDetermine&id={file_id}&species={species}` (GET)
- **结果获取接口**：`https://www.bdbe.cn/kun/api/result?id={task_id}` (GET)
- **文件下载接口**：`https://www.bdbe.cn/kun/api/result/download?link={link}` (GET)

## Notes

- 支持的文件格式：CSV格式
- 分析过程可能需要较长时间，脚本会自动轮询等待结果
- 结果包含样本性别判定列表和CSV格式的结果文件
- 下载的结果文件默认保存在上传文件所在目录，也可通过output_dir参数指定