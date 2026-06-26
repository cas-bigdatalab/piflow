---
name: weighted_sampler
description: 加权采样算子。读取JSONL记录，按数值型权重字段执行随机采样，支持有放回和无放回两种模式。当用户提到加权抽样、按权重抽样、优先级采样、重要性重采样等需求时使用此skill。即使用户没有明确说出“加权采样”，只要任务涉及按记录权重选择样本，就应该使用此skill。不负责按类别分层均衡、普通随机采样或文本内容过滤。
name_zh: 加权采样算子
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: weight_field
  type: string
  required: true
  description: 权重字段名
- name: sample_size
  type: string
  required: true
  description: 采样数量
- name: with_replacement
  type: string
  required: false
  default: "False"
  description: 有放回采样
- name: seed
  type: string
  required: false
  default: "42"
  description: 随机种子
- name: log_file
  type: string
  required: false
  description: 日志文件路径
output_params:
- name: output
  type: jsonl_file
  description: 加权采样结果JSONL文件
tag: 切分与采样
---

# WeightedSampler - 加权采样算子

## 功能概述
根据记录的权重字段进行加权随机采样，权重越大的记录被选中的概率越高。支持有放回和无放回两种模式，适用于重要性采样、优先级抽样等场景。

## 触发条件
- 用户提到加权抽样、按权重抽样、优先级采样、重要性重采样
- 需要从JSONL记录中按权重选择样本
- 需要在保留字段结构的前提下减少样本量

## 核心参数说明

### 必需参数
- `--input`：输入JSONL文件路径
- `--output`：输出JSONL文件路径
- `--weight_field`：权重字段名
- `--sample_size`：采样数量

### 可选参数
- `--with_replacement`：有放回采样，默认无放回
- `--seed`：随机种子，默认 `42`
- `--log_file`：日志文件路径

## 输入文件格式
输入文件必须是JSONL，每行一个JSON对象。`weight_field` 对应的值必须能转换为数值；非数值、缺失、或小于等于 0 的记录会被跳过。

## 使用方法
```bash
python scripts/run_weighted_sampler.py --input data.jsonl --output sampled.jsonl --weight_field priority_score --sample_size 1000 --seed 42
```

## 输出示例
```jsonl
{"id": 12, "score": 101, "_sample_weight": 101.0, "_sample_normalized_weight": 0.22911217218528326}
{"id": 2, "score": 120, "_sample_weight": 120.0, "_sample_normalized_weight": 0.2722124818042969}
```

## 环境要求
- Python 3.10+
- 输入文件可由本地脚本或上游算子生成

## 注意事项
- 无放回模式下，采样结果不会重复
- 有放回模式下，同一条记录可能被抽中多次
- 输出会附带 `_sample_weight` 和 `_sample_normalized_weight`
