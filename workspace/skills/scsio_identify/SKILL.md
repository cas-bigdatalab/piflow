---
name: scsio_identify
description: 用于识别海洋生物的技能。当用户希望识别海洋生物、上传图片识别图中海洋生物等情况时触发。
compatibility:
  - python
  - requests

input_params:
  - name: image_file
    type: string
    required: true
    description: 图片文件路径

  - name: threshold
    type: float
    required: false
    default: 0.1
    description: 相似度阈值，用于筛选高置信度结果

output_params:
  - name: result
    type: string
    description: 海洋生物识别结果（文本格式）
---

# scsio_identify Skill

## 功能描述
用户通过上传一个图片（二进制），调用中国科学院南海海洋研究所的海洋生物识别服务，获得图片识别结果并格式化展示。

## 核心功能
- 支持图片文件上传
- 调用外部海洋生物识别服务
- 格式化展示识别结果
- 按相似度排序展示结果

## 参数说明
- `image_file`：图片文件路径（必要参数）
- `threshold`：相似度阈值（可选，默认0.1），用于筛选高置信度结果

## 依赖
- requests

## 使用示例

### 基本使用
```bash
python scripts/scsio_identify.py --image_file fish.jpg
```

### 设置相似度阈值
```bash
python scripts/scsio_identify.py --image_file fish.jpg --threshold 0.3
```

## 输入输出示例

#### 输入
```bash
python scripts/scsio_identify.py --image_file dog.jpg
```

#### 输出
```
识别结果：
1. 中华田园犬 - 相似度: 46.79%
2. 西藏猎犬 - 相似度: 23.34%
3. 博美 - 相似度: 6.66%
4. 串串狗 - 相似度: 6.63%
5. 日本柴犬 - 相似度: 4.39%
6. 德国狐狸犬 - 相似度: 2.85%

日志ID: 2031193976357444866
```

## 注意事项
- 支持的图片格式：jpg、png等常见图片格式
- 图片大小限制：建议不超过5MB
- 识别结果按相似度从高到低排序
- 可以通过设置阈值过滤低置信度结果