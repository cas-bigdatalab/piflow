---
name: zh_en_mixed_deduplicator_lightweight
description: |
  轻量中英文混杂去重工具。读取 TXT、JSON 或 JSONL 文档，将正文拆分为句段，识别中文与英文之间的翻译对照或语义等价内容，删除重复句段并输出精简结果。
  当用户提到中英文混杂去重、双语对照去重、翻译段落去重、中文英文重复内容或资源受限环境下的双语语义去重等需求时使用此 skill。
  即使用户没有明确说出“轻量中英文混杂去重”，只要任务涉及单篇文档内中文与英文语义相同内容的识别、清理或压缩，并需要降低模型存储或推理资源占用，就应该使用此 skill。
name_zh: 轻量中英文混杂去重算子
input_params:
  - name: input
    type: string
    required: true
    description: 中英文混杂文档路径，支持 TXT、JSON 和 JSONL
  - name: output
    type: string
    required: true
    description: 去重后文档的输出路径，扩展名应与输入格式一致
  - name: text_key
    type: string
    required: false
    default: text
    description: 'JSON 或 JSONL 每条记录中用于保存待去重正文的字段名称；例如输入记录为 {"content": "..."} 时填写 content。TXT 输入不使用此参数'
  - name: similarity_threshold
    type: number
    required: false
    default: 0.75
    description: 中文段落与英文段落判为语义重复的余弦相似度阈值，范围为 0 到 1
  - name: keep
    type: string
    required: false
    default: zh
    description: 对语义重复的中英文段落保留中文或英文内容，可选 zh 或 en
output_params:
  - name: output
    type: file
    description: 删除中英文语义重复段落后的 TXT、JSON 或 JSONL 文档
tag: 数据清洗
publisher: COMMUNITY
---

# 轻量中英文混杂去重

## 功能说明

该算子面向中英文混合排版文档，将正文按换行和中英文句末边界拆分为句段，比较中文句段与英文句段的语义相似度。相似度达到阈值的跨语种句段会被视为翻译对照或语义重复内容，并按保留策略只留下其中一个句段。

适用于双语科研文献、外文翻译文稿、中英文对照实验说明和双语注释资料。TXT 作为单篇文档处理；JSON 对象、对象数组和 JSONL 中的每条记录分别去重，不会跨记录删除内容。它只比较中文与英文句段之间的重复关系，不会因单语句段相近而删除内容。

## 处理逻辑

1. 读取预置的 INT8 ONNX 模型和分词器。
2. 读取 TXT 全文，或逐个读取 JSON 对象、对象数组及 JSONL 记录中 `text_key` 指定的正文。
3. 按换行及中英文句末标点拆分句段，并识别每个句段的主导语言。
4. 生成句段语义向量并归一化。
5. 仅在同一文档或记录的中文句段与英文句段之间计算余弦相似度，并按相似度由高到低进行一对一匹配。
6. 根据 `keep` 保留每对中的中文或英文句段，并将结果写入 `output`。

## 使用方法

```bash
python scripts/run_zh_en_mixed_deduplicator_lightweight.py \
  --input "{input}" \
  --output "{output}" \
  --text_key "{text_key}" \
  --similarity_threshold "{similarity_threshold}" \
  --keep "{keep}"
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `--input` | 是 | - | 中英文混杂 TXT、JSON 或 JSONL 文档路径。 |
| `--output` | 是 | - | 输出文档路径；须与输入使用相同扩展名。 |
| `--text_key` | 否 | `text` | JSON/JSONL 每条记录中用于保存待去重正文的字段名称；例如记录为 `{"content": "..."}` 时填写 `content`。请填写字段名称，不要填写正文内容；TXT 输入不使用此参数。 |
| `--similarity_threshold` | 否 | `0.75` | 跨语种语义重复的判定阈值，值越高匹配越严格。 |
| `--keep` | 否 | `zh` | 重复组保留语种：`zh` 保留中文句段，`en` 保留英文句段。 |

## 输入文件说明

TXT 文件作为单篇文档处理，换行和句末标点均可形成句段边界。JSON 支持顶层对象、对象数组或字符串；JSONL 逐行处理对象。对象中的正文由 `text_key` 指定。

## 输出结果

TXT 输入输出去重后的正文。JSON/JSONL 会保留对象中的其他字段，并以去重后的正文更新 `text_key` 指定字段。控制台会输出处理文档数、中文句段数、英文句段数和已删除的跨语种重复句段数。

## 依赖

```bash
pip install numpy onnxruntime transformers
```

该轻量版使用 ONNX Runtime 执行预置的 INT8 量化模型，以降低模型存储和 CPU 推理资源占用。模型文件完整时直接加载；首次运行或模型不完整时，会自动解压 `scripts/assets/onnx/model_quantized.onnx.gz`，运行过程无需访问网络下载模型。

## 注意事项

- 每个句段仍按中英文字符数量判断主导语言；一个不可拆分的句段若同时混有两种语言，只按主导语言参与匹配。
- JSON 数组和 JSONL 按记录独立去重，不做跨记录样本去重。
- 阈值应结合语料质量调整。翻译质量差异较大时可适度降低阈值，术语高度敏感时应提高阈值。
- 输出目录会自动创建，输入输出扩展名必须一致。
- 首次解压需要为临时模型预留足够磁盘空间；同一 skill 的并发首次调用会通过压缩包文件锁串行解压。
