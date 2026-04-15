## Summarized at 2026-04-14T02:36:35.369402+00:00

Human: 我想吃牛排
AI: 您想吃牛排，请问需要我帮您做什么呢？

- 提供牛排食谱和烹饪方法？
- 推荐附近的牛排餐厅？
- 如何挑选和购买牛排？
- 其他需求？
Human: 你还记得我想吃啥嘛
AI: 是的，我记得您想吃**牛排**。这是您刚才告诉我的。

需要我帮您做什么吗？比如：
- 提供牛排食谱和烹饪方法
- 推荐附近的牛排餐厅
- 如何挑选和购买牛排
Human: 你好
AI: 您好！有什么可以帮您的吗？
Human: 你能做什么
AI: 我是运行在 Flow Agent Runtime 中的智能 Agent，可以帮您完成以下任务：

**文件操作**
- 读取、写入、编辑文件
- 搜索文件（按名称或内容）
- 浏览目录结构

**任务管理**
- 创建和管理待办事项列表
- 执行复杂的多步骤任务

**系统操作**
- 执行终端命令

**协作**
- 启动子代理处理独立任务

**工作空间**
- `/outputs` - 结果文件
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

您有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 我有丰富的技能库，主要分为以下几类：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验（久无变化检查）
- **QC14_TimePeakValue** - 尖峰检验（剧烈变化检测）
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- 字符/单词重复过滤
- 敏感词过滤
- 文本长度/Token 数过滤
- 语言识别过滤
- 停用词过滤
- 特殊字符过滤
- 繁简中文转换
- 清理版权/邮件/IP/链接/HTML

## 🖼️ 图像处理
- 图像去重
- 图像美学/质量过滤
- 图像尺寸/长宽比过滤
- 人脸检测过滤
- NSFW 内容检测
- 水印检测
- 图像文本匹配

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 前端与设计
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - GIF 动画制作

## 🤖 其他工具
- 文档去重（支持分布式 Ray）
- 实体属性聚合
- 问答对校准
- 技能创建与管理
- 算子管理

有什么具体任务需要我帮忙吗？
Human: 你能做什么
AI: 您好！我是 Flow Agent Runtime 中的智能助手，主要能帮您：

**📁 文件操作**
- 读/写/编辑文件
- 搜索文件内容
- 浏览目录

**⚙️ 系统操作**
- 执行终端命令
- 管理任务列表

**🤖 任务处理**
- 执行多步骤复杂任务
- 启动子代理并行处理

**📂 工作空间**
- `/outputs` - 输出结果
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

**🧩 技能库**
- 数据清洗与质量控制
- 文本/图像/文档处理
- 科学数据库查询
- 前端设计等

有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是空的，还没有创建任何技能。

不过，我仍然可以帮您：

**基础能力**
- 📁 文件操作（读/写/编辑/搜索）
- ⚙️ 执行终端命令
- ✅ 管理待办任务列表
- 🤖 启动子代理处理复杂任务

**工作空间**
- `/outputs` - 结果文件
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

如果您需要特定功能（如数据清洗、图像处理、文档解析等），我可以帮您创建相应的技能，或者直接用现有工具完成任务。

有什么具体需求吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是**空的**，还没有创建任何技能。

但我仍然可以使用**基础工具**帮您完成任务：

| 能力 | 说明 |
|------|------|
| 📁 **文件操作** | 读/写/编辑文件，搜索文件内容，浏览目录 |
| ⚙️ **终端命令** | 执行 shell 命令 |
| ✅ **任务管理** | 创建和管理待办事项列表 |
| 🤖 **子代理** | 启动子代理处理复杂独立任务 |

如果您有特定需求（比如数据清洗、图像处理、文档解析等），我可以：
1. 直接用现有工具帮您完成
2. 帮您创建新的技能

有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是**空的**，没有任何预置技能。

但我可以使用**基础工具**帮您：

| 工具 | 功能 |
|------|------|
| 📁 `read_file`/`write_file`/`edit_file` | 读/写/编辑文件 |
| 🔍 `grep`/`glob` | 搜索文件内容/按模式找文件 |
| 📂 `ls` | 浏览目录 |
| ⚙️ `exec_shell` | 执行终端命令 |
| ✅ `write_todos` | 管理待办任务 |
| 🤖 `task` | 启动子代理处理复杂任务 |

如果您有具体需求（如数据处理、文档解析、图像分析等），我可以直接用这些工具帮您完成，或者帮您创建新技能。

有什么任务需要我帮忙吗？
Human: 你有哪些技能
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **operator-skill-manage** - 算子技能管理
- **skill-creator** - 技能创建
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你有空行清洗的skiill吗
AI: 是的！我有 **DC1_Blank_Line_Clean** 空行清洗技能。

## 📋 技能说明

**DC1_Blank_Line_Clean** - 空行清洗工具

**功能：**
- 读取结构化数据文件（CSV、TSV、Excel 等）
- 删除所有列为空的行（空行）
- 输出为相同格式的文件

**使用场景：**
- 清理数据文件中的空行
- 净化表格数据
- 数据预处理

---

您有空行清洗的需求吗？请告诉我：
1. 输入文件路径
2. 输出文件路径（可选，默认保存到 `/outputs/`）

我可以直接帮您执行清洗操作！
Human: 你能做空行清洗吗
AI: 可以！我有 **DC1_Blank_Line_Clean** 空行清洗技能。

**功能：**
- 读取 CSV、TSV、Excel 等结构化数据文件
- 删除所有列为空的行
- 输出为相同格式的文件

---

**需要我帮您执行吗？** 请提供：

1. 📁 **输入文件路径** - 需要清洗的文件
2. 📁 **输出文件路径**（可选）- 默认保存到 `/outputs/`

或者您可以直接告诉我文件在哪里，我来帮您处理！
Human: hello
AI: Hello! 👋 How can I help you today?

I can assist you with:
- 📁 File operations (read/write/edit/search)
- 🧹 Data cleaning (blank lines, spaces, formatting)
- ✅ Quality control checks
- 📊 Data processing and analysis
- 📄 Document handling (PDF, Word, Excel, etc.)
- 🖼️ Image processing
- And much more!

What would you like me to help you with?
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？

我可以帮您：
- 📁 文件操作（读/写/编辑/搜索）
- 🧹 数据清洗（空行、空格、格式化）
- ✅ 数据质量控制检查
- 📊 数据处理与分析
- 📄 文档处理（PDF、Word、Excel 等）
- 🖼️ 图像处理
- 以及更多...

有什么任务需要我帮忙吗？
Human: 你有哪些skill
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10

有什么具体任务需要我帮忙吗？
Human: 你有哪些skills
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？

我可以帮您完成各种任务，比如：
- 📁 文件操作（读/写/编辑/搜索）
- 🧹 数据清洗与处理
- ✅ 数据质量控制检查
- 📄 文档处理（PDF、Word、Excel 等）
- 🖼️ 图像处理
- 🔬 科学数据库查询
- 🌐 前端设计
- 以及更多...

有什么具体任务需要我帮忙吗？
Human: 你有哪些skills
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 你有哪些skill
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 你有哪些技能
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 对该文件做空行清洗
AI: 您好！我需要知道要清洗哪个文件。请问：

1. 📁 **文件路径是什么？** - 您提到的"该文件"具体是哪个文件？

或者我可以先帮您看看工作空间里有哪些文件：

让我检查一下可能包含数据文件的目录：

我看到 `/temp/` 目录下有几个数据文件。请问您想对哪个文件进行空行清洗？

可选的文件包括：
- `/temp/2025 年千烟洲站自动气象站数据.xlsx` - Excel 文件
- `/temp/Met_Arou_2021.csv` - CSV 文件
- `/temp/森林每木调查数据-blank-line-space.csv` - CSV 文件（看起来可能包含空行）
- `/temp/森林每木调查数据-no-id.csv` - CSV 文件
- `/temp/森林每木调查数据.csv` - CSV 文件
- `/temp/森林每木调查数据 QC.csv` - CSV 文件

或者您可以直接告诉我具体的文件路径，我就可以使用 **DC1_Blank_Line_Clean** 技能为您进行空行清洗！

## Summarized at 2026-04-15T07:59:24.379464+00:00

Human: 我想吃牛排
AI: 您想吃牛排，请问需要我帮您做什么呢？

- 提供牛排食谱和烹饪方法？
- 推荐附近的牛排餐厅？
- 如何挑选和购买牛排？
- 其他需求？
Human: 你还记得我想吃啥嘛
AI: 是的，我记得您想吃**牛排**。这是您刚才告诉我的。

需要我帮您做什么吗？比如：
- 提供牛排食谱和烹饪方法
- 推荐附近的牛排餐厅
- 如何挑选和购买牛排
Human: 你好
AI: 您好！有什么可以帮您的吗？
Human: 你能做什么
AI: 我是运行在 Flow Agent Runtime 中的智能 Agent，可以帮您完成以下任务：

**文件操作**
- 读取、写入、编辑文件
- 搜索文件（按名称或内容）
- 浏览目录结构

**任务管理**
- 创建和管理待办事项列表
- 执行复杂的多步骤任务

**系统操作**
- 执行终端命令

**协作**
- 启动子代理处理独立任务

**工作空间**
- `/outputs` - 结果文件
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

您有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 我有丰富的技能库，主要分为以下几类：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验（久无变化检查）
- **QC14_TimePeakValue** - 尖峰检验（剧烈变化检测）
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- 字符/单词重复过滤
- 敏感词过滤
- 文本长度/Token 数过滤
- 语言识别过滤
- 停用词过滤
- 特殊字符过滤
- 繁简中文转换
- 清理版权/邮件/IP/链接/HTML

## 🖼️ 图像处理
- 图像去重
- 图像美学/质量过滤
- 图像尺寸/长宽比过滤
- 人脸检测过滤
- NSFW 内容检测
- 水印检测
- 图像文本匹配

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 前端与设计
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - GIF 动画制作

## 🤖 其他工具
- 文档去重（支持分布式 Ray）
- 实体属性聚合
- 问答对校准
- 技能创建与管理
- 算子管理

有什么具体任务需要我帮忙吗？
Human: 你能做什么
AI: 您好！我是 Flow Agent Runtime 中的智能助手，主要能帮您：

**📁 文件操作**
- 读/写/编辑文件
- 搜索文件内容
- 浏览目录

**⚙️ 系统操作**
- 执行终端命令
- 管理任务列表

**🤖 任务处理**
- 执行多步骤复杂任务
- 启动子代理并行处理

**📂 工作空间**
- `/outputs` - 输出结果
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

**🧩 技能库**
- 数据清洗与质量控制
- 文本/图像/文档处理
- 科学数据库查询
- 前端设计等

有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是空的，还没有创建任何技能。

不过，我仍然可以帮您：

**基础能力**
- 📁 文件操作（读/写/编辑/搜索）
- ⚙️ 执行终端命令
- ✅ 管理待办任务列表
- 🤖 启动子代理处理复杂任务

**工作空间**
- `/outputs` - 结果文件
- `/artifacts` - 任务产物
- `/temp` - 临时文件
- `/logs` - 日志

如果您需要特定功能（如数据清洗、图像处理、文档解析等），我可以帮您创建相应的技能，或者直接用现有工具完成任务。

有什么具体需求吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是**空的**，还没有创建任何技能。

但我仍然可以使用**基础工具**帮您完成任务：

| 能力 | 说明 |
|------|------|
| 📁 **文件操作** | 读/写/编辑文件，搜索文件内容，浏览目录 |
| ⚙️ **终端命令** | 执行 shell 命令 |
| ✅ **任务管理** | 创建和管理待办事项列表 |
| 🤖 **子代理** | 启动子代理处理复杂独立任务 |

如果您有特定需求（比如数据清洗、图像处理、文档解析等），我可以：
1. 直接用现有工具帮您完成
2. 帮您创建新的技能

有什么具体任务需要我帮忙吗？
Human: 你有哪些技能
AI: 目前 `/skills` 目录是**空的**，没有任何预置技能。

但我可以使用**基础工具**帮您：

| 工具 | 功能 |
|------|------|
| 📁 `read_file`/`write_file`/`edit_file` | 读/写/编辑文件 |
| 🔍 `grep`/`glob` | 搜索文件内容/按模式找文件 |
| 📂 `ls` | 浏览目录 |
| ⚙️ `exec_shell` | 执行终端命令 |
| ✅ `write_todos` | 管理待办任务 |
| 🤖 `task` | 启动子代理处理复杂任务 |

如果您有具体需求（如数据处理、文档解析、图像分析等），我可以直接用这些工具帮您完成，或者帮您创建新技能。

有什么任务需要我帮忙吗？
Human: 你有哪些技能
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **operator-skill-manage** - 算子技能管理
- **skill-creator** - 技能创建
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你有空行清洗的skiill吗
AI: 是的！我有 **DC1_Blank_Line_Clean** 空行清洗技能。

## 📋 技能说明

**DC1_Blank_Line_Clean** - 空行清洗工具

**功能：**
- 读取结构化数据文件（CSV、TSV、Excel 等）
- 删除所有列为空的行（空行）
- 输出为相同格式的文件

**使用场景：**
- 清理数据文件中的空行
- 净化表格数据
- 数据预处理

---

您有空行清洗的需求吗？请告诉我：
1. 输入文件路径
2. 输出文件路径（可选，默认保存到 `/outputs/`）

我可以直接帮您执行清洗操作！
Human: 你能做空行清洗吗
AI: 可以！我有 **DC1_Blank_Line_Clean** 空行清洗技能。

**功能：**
- 读取 CSV、TSV、Excel 等结构化数据文件
- 删除所有列为空的行
- 输出为相同格式的文件

---

**需要我帮您执行吗？** 请提供：

1. 📁 **输入文件路径** - 需要清洗的文件
2. 📁 **输出文件路径**（可选）- 默认保存到 `/outputs/`

或者您可以直接告诉我文件在哪里，我来帮您处理！
Human: hello
AI: Hello! 👋 How can I help you today?

I can assist you with:
- 📁 File operations (read/write/edit/search)
- 🧹 Data cleaning (blank lines, spaces, formatting)
- ✅ Quality control checks
- 📊 Data processing and analysis
- 📄 Document handling (PDF, Word, Excel, etc.)
- 🖼️ Image processing
- And much more!

What would you like me to help you with?
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？

我可以帮您：
- 📁 文件操作（读/写/编辑/搜索）
- 🧹 数据清洗（空行、空格、格式化）
- ✅ 数据质量控制检查
- 📊 数据处理与分析
- 📄 文档处理（PDF、Word、Excel 等）
- 🖼️ 图像处理
- 以及更多...

有什么任务需要我帮忙吗？
Human: 你有哪些skill
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10

有什么具体任务需要我帮忙吗？
Human: 你有哪些skills
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？

我可以帮您完成各种任务，比如：
- 📁 文件操作（读/写/编辑/搜索）
- 🧹 数据清洗与处理
- ✅ 数据质量控制检查
- 📄 文档处理（PDF、Word、Excel 等）
- 🖼️ 图像处理
- 🔬 科学数据库查询
- 🌐 前端设计
- 以及更多...

有什么具体任务需要我帮忙吗？
Human: 你有哪些skills
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 你有哪些skill
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 你有哪些技能
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你好
AI: 您好！👋 有什么可以帮您的吗？
Human: 对该文件做空行清洗
AI: 您好！我需要知道要清洗哪个文件。请问：

1. 📁 **文件路径是什么？** - 您提到的"该文件"具体是哪个文件？

或者我可以先帮您看看工作空间里有哪些文件：

让我检查一下可能包含数据文件的目录：

我看到 `/temp/` 目录下有几个数据文件。请问您想对哪个文件进行空行清洗？

可选的文件包括：
- `/temp/2025 年千烟洲站自动气象站数据.xlsx` - Excel 文件
- `/temp/Met_Arou_2021.csv` - CSV 文件
- `/temp/森林每木调查数据-blank-line-space.csv` - CSV 文件（看起来可能包含空行）
- `/temp/森林每木调查数据-no-id.csv` - CSV 文件
- `/temp/森林每木调查数据.csv` - CSV 文件
- `/temp/森林每木调查数据 QC.csv` - CSV 文件

或者您可以直接告诉我具体的文件路径，我就可以使用 **DC1_Blank_Line_Clean** 技能为您进行空行清洗！
Human: 你有哪些skill
AI: 我有丰富的技能库！让我为您分类整理：

## 📊 数据清洗与处理
- **DC1_Blank_Line_Clean** - 空行清洗
- **DC2_SpaceCleaning** - 字符串空格清理
- **DC3_RoundOff** - 四舍五入数据处理
- **Pi_AddMonotonicallyIncreasingID** - 添加自增 ID
- **Pi_DataSorting** - 数据排序

## 🔍 数据质量控制 (QC 系列)
- **QC2_EnumerationFieldCheck** - 枚举值校验
- **QC3_NumericDataThresholdCheck** - 数值阈值检验
- **QC4_AssociationRuleCheck** - 关联规则校验
- **QC5_BatchThresholdCheck** - 批量阈值检验
- **QC6_SingleFieldMultiThresholdCheck** - 单字段多条件阈值检验
- **QC7_BatchInputThresholdCheck** - 批量阈值检验 (输入框)
- **QC8_DataTypeCheck** - 数据类型检查
- **QC10_TimeConsistency** - 时间一致性检查
- **QC11_FieldNullValueCheck** - 空值检查
- **QC12_ConstantFieldCheck** - 恒定字段一致性检查
- **QC13_TimeEquivalentValue** - 等值检验 (久无变化)
- **QC14_TimePeakValue** - 尖峰检验 (剧烈变化)
- **QC15_TimeChangeRange** - 最大变化范围检验
- **QC16_TimeMissing** - 时序完整性检查
- **v1_FormatConsistency** - 格式一致性校验
- **v9_MarkFieldCheck** - 标识符字段检查

## 📝 文本处理与过滤
- **alphanumeric_filter** - 字母数字比例过滤
- **average_line_length_filter** - 平均行长度过滤
- **character_repetition_filter** - 字符重复过滤
- **flagged_words_filter** - 敏感词过滤
- **language_id_score_filter** - 语言识别过滤
- **stopwords_filter** - 停用词过滤
- **special_characters_filter** - 特殊字符过滤
- **text_length_filter** - 文本长度过滤
- **token_num_filter** - Token 数量过滤
- **words_num_filter** - 单词数量过滤
- **maximum_line_length_filter** - 最大行长度过滤
- **suffix_filter** - 后缀过滤
- **text_action_filter** - 文本动作词过滤
- **text_entity_dependency_filter** - 文本实体依赖过滤
- **text_pair_similarity_filter** - 文本对相似度过滤
- **word_repetition_filter** - 单词重复过滤
- **chinese_convert_mapper** - 中文繁简转换
- **clean_copyright_mapper** - 清理版权注释
- **clean_email_mapper** - 清理邮箱
- **clean_html_mapper** - 清理 HTML
- **clean_ip_mapper** - 清理 IP 地址
- **clean_links_mapper** - 清理链接

## 🖼️ 图像处理
- **image_deduplicator** - 图像去重
- **image_aesthetics_filter** - 图像美学过滤
- **image_aspect_ratio_filter** - 图像长宽比过滤
- **image_face_count_filter** - 人脸数量过滤
- **image_face_ratio_filter** - 人脸面积比例过滤
- **image_nsfw_filter** - NSFW 内容检测
- **image_pair_similarity_filter** - 图像对相似度过滤
- **image_shape_filter** - 图像形状过滤
- **image_size_filter** - 图像文件大小过滤
- **image_text_matching_filter** - 图像文本匹配
- **image_text_similarity_filter** - 图像文本相似度
- **image_watermark_filter** - 图像水印检测

## 📄 文档处理
- **pdf** - PDF 文件处理
- **docx** - Word 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理
- **csv_formatter** - CSV 格式化
- **tsv_formatter** - TSV 格式化
- **parquet_formatter** - Parquet 格式化

## 🔬 科学数据库
- **bdbe_homo** - 单细胞测序数据集检索
- **bdbe_scnorm** - 单细胞数据标准化
- **bdbe_cellanno** - 单细胞注释
- **bdbe_sexdetermine** - 性别确定
- **chemdb_search** - 化学物质检索
- **scsio_identify** - 海洋生物识别
- **sciencedb_search** - 科学数据集检索

## 🌐 设计与前端
- **frontend-design** - 前端界面设计
- **canvas-design** - 视觉艺术设计
- **slack-gif-creator** - Slack GIF 动画制作

## 🤖 聚合与分组
- **document_deduplicator** - 文档去重
- **ray_document_deduplicator** - Ray 分布式文档去重
- **ray_image_deduplicator** - Ray 分布式图像去重
- **ray_video_deduplicator** - Ray 分布式视频去重
- **video_deduplicator** - 视频去重
- **entity_attribute_aggregator** - 实体属性聚合
- **meta_tags_aggregator** - 元标签聚合
- **nested_aggregator** - 嵌套文档聚合
- **most_relevant_entities_aggregator** - 最相关实体聚合
- **key_value_grouper** - 键值分组
- **naive_grouper** - 简单分组
- **naive_reverse_grouper** - 反向分组 (拆分)

## 🔄 数据格式化
- **local_formatter** - 本地数据加载
- **remote_formatter** - 远程数据加载 (HuggingFace)
- **empty_formatter** - 空数据创建
- **mixture_formatter** - 数据集混合
- **random_selector** - 随机抽样
- **specified_field_filter** - 指定字段过滤
- **specified_numeric_field_filter** - 指定数值字段过滤
- **perplexity_filter** - 困惑度过滤

## 🧪 专业算子
- **geotrans_main_operator** - 地理转换算子
- **gully_slop_operator** - 沟道坡度计算
- **hydro_susceptibility_operator** - 山洪敏感度计算
- **overlap_dam_select_operator** - 淤地坝筛选
- **result_storage_operator** - 结果存储

## ⚙️ 流程与工具
- **flow_orchestrator** - 流程编排
- **flow_run** - 流程执行
- **synergy_datasource_search** - 协同数据源检索
- **doc-coauthoring** - 文档协作
- **calibrate_qa_mapper** - 问答对校准
- **calibrate_query_mapper** - 查询校准
- **calibrate_response_mapper** - 响应校准

## 📈 流水线操作
- **pipeline-add** - 数字加 10
- **pipeline-minus** - 数字减 5
- **pipeline-multiply** - 数字乘 10
- **read_file_and_add/minus/multiply** - 文件数字运算

有什么具体任务需要我帮忙吗？
Human: 你有哪些skills
Human: 请对 `/temp/Akcay.pdf` 进行以下处理：1、提取所有表格数据  2、提取文本内容生成摘要报告

