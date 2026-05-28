---
name: piflow-skill-generator
description: |
  PiFlow 技能生成器。根据当前 workspace/skills 的本地约定和 references/piflow_skill_template.md 通用模板创建、更新或校验 PiFlow-compatible skill，包括 UTF-8 编码的 SKILL.md、DAG 可读的 input_params/output_params、version/category/tag 元数据、skill.json、scripts/references/assets 资源目录，以及本地校验脚本。仅在用户明确要求生成或保存 skill，或某次数据处理任务已经完成并需要把已验证成功的操作流程沉淀为 skill 时使用；默认不要因为“可能需要 skill”或“当前能力不足”而优先触发此 skill。
name_zh: PiFlow 算子生成器
version: 1.1.2
category: skill_generation
allowed-tools:
  - process

input_params:
  - name: spec_path
    role: input_data
    type: string
    required: true
    description: 技能规格 JSON 文件路径，必须使用 UTF-8 编码

  - name: output_root
    role: output_data
    type: string
    required: false
    default: skills
    description: 输出根目录；deepagent 虚拟文件环境，默认写入 workspace/skills

  - name: overwrite
    role: data
    type: bool
    required: false
    default: false
    description: 是否覆盖已存在的技能目录

output_params:
  - name: skill_dir
    role: output_data
    type: directory
    description: 生成后的技能目录

  - name: skill_md
    role: output_data
    type: markdown_file
    description: 生成后的 SKILL.md
tag: 算子生成
---

# PiFlow Skill Generator

## 核心规则

除去对运行/测试时的产物进行分析，其他工作应尽量提前计划和生成，避免在安装或测试阶段才发现文档不完整、脚本缺失或资源错误。技能生成器的目标是一次性生成一个完整、可靠、符合约定的技能目录，能直接被 PiFlow 识别和使用，但它不是默认优先入口。

生成能被 PiFlow 理解的技能目录。所有文本文件必须以 UTF-8 读写，尤其是中文内容；Python 读写文件时显式使用 `encoding="utf-8"`，JSON 输出使用 `ensure_ascii=False`。

按库内技能的粒度控制内容：`SKILL.md` 只放触发、流程和必要契约；可执行逻辑放 `scripts/`；较长规则、字段说明和领域资料放 `references/`；模板、图标、示例素材放 `assets/`。

生成正文时优先参照 `references/piflow_skill_template.md`。当 spec 中提供 `core_features`、`trigger_conditions`、`processing_logic`、`supported_formats`、`output_structure`、`output_examples` 等字段时，将它们填入模板对应章节。

本技能必须能在没有其他技能辅助的环境中独立生成可靠技能：只依赖当前技能目录内的 `SKILL.md`、`references/piflow_skill_template.md`、`scripts/generate_piflow_skill.py` 和 `scripts/validate_piflow_skill.py`。生成时不要假设另一个 skill 会补全文档、脚本或元数据，也不要把“当前能力不足”作为优先切换到本技能的理由；应先完成当前数据处理任务，再决定是否沉淀为 skill。

本技能的触发优先级应降低到“任务完成后的沉淀动作”或“用户手动指定动作”。如果当前任务本质是数据清洗、转换、分析、抽取、校验、聚合、导入导出或其他处理流程，应先直接完成任务本身；只有当流程已经跑通、结果已验证，且用户明确要求生成 skill，或系统在任务完成后询问用户是否要把本次成功流程保存为 skill 时，才进入技能生成阶段。

在涉及安装、环境准备或可执行脚本验证时，优先完成最小必要依赖，再运行一个简单冒烟测试确认关键入口可执行、基础参数可解析、输出路径可写。若安装或测试失败，允许自动重试，单个阶段最多重试 5 次；若 5 次后仍失败，停止流程并把失败原因、失败步骤和最后一次错误返回给用户。

安装依赖或配置前置环境时，若不明确安装的流程或操作，需要调用网络工具获取安装指南或官方文档，或者直接调用搜索查询安装步骤，不要假设已经知道如何安装或配置。

## 路径规则

deepagent 的虚拟文件环境以 `workspace` 为根。生成的技能必须放在 `workspace/skills/<skill-name>`，这样 PiFlow 才能发现。

- 默认 `output_root` 使用 `skills`，表示 `<workspace>/skills`。
- 如果用户传入旧路径 `workspace/skills` 或 `flow-deepagents/workspace/skills`，脚本会归一化为当前 deepagent workspace 下的 `skills`。
- `spec_path`、`icon`、`script.source`、`references[].source`、`assets[].source` 可以使用相对路径；脚本会先按当前工作目录解析，再按 deepagent workspace 根解析。
- 不要把生成目录写到仓库外层、`flow-deepagents/workspace/workspace/skills` 或 `workspace/skills/skills`。

## PiFlow 技能结构

每个技能目录至少包含：

```text
skill-name/
├── SKILL.md
├── skill.json             # 推荐，DAG 执行/画板读取的结构化元数据
├── scripts/               # 推荐，稳定可执行逻辑
├── references/            # 可选，按需读取的长文档
└── assets/
    └── icon.png           # 推荐，技能中心图标
```

### SKILL.md

`SKILL.md` 由 YAML frontmatter 和 Markdown body 组成。

- `name`：必须与目录名完全一致。
- `description`：主要触发入口。必须同时说明技能做什么、用户在什么表达或场景下应触发。触发信息写在这里，不要只写在正文。
- `version`：技能版本，默认 `1.0.0`。
- `category`：面向技能中心或业务域的分类。
- `input_params`：PiFlow DAG 面板读取的输入参数列表，必须保留。
- `output_params`：PiFlow DAG 面板读取的输出参数列表，必须保留。
- `allowed-tools`、`compatibility`、`license`、`metadata`：仅在确实需要时添加。
- `tag`：面向 DAG 面板的技能类型；当前入库逻辑会读取 `tag` 作为 `skill_type`。

参数项使用：

```yaml
- name: input_path
  type: string
  role: input_data
  required: true
  default: optional-default
  description: 输入文件路径
```

参数 `role` 可选，建议在 DAG 技能中填写：

- `input_data`：输入数据文件或目录。
- `output_data`：输出数据文件或目录。
- `data`：普通配置参数。

### skill.json

当 `skill_json` 未显式设为 `false` 时生成。该文件用于 DAG 执行链路和画板解析，包含：

- `name`、`version`、`description`
- `language`
- `script_path`
- `entrypoint`
- `input_params`、`output_params`，其中参数包含 `role`
- `command_template`
- 可选 `category`、`tag`


只在用户或 spec 明确提供时写入 `dependencies` 或 `policy` 等扩展字段。

### Bundled Resources

- `scripts/`：放确定性脚本、算子封装、批处理逻辑。脚本应可通过 `python scripts/<name>.py ...` 调用，并使用 UTF-8 读写。
- `references/`：放长规则、字段字典、API 说明、数据 schema、复杂示例。正文中必须说明何时读取哪个引用文件。
- `assets/`：放图标、模板、示例素材、字体或输出需要复制的资源。PiFlow 技能中心优先寻找 `assets/icon.png`。

不要生成与执行无关的 `README.md`、安装指南、变更日志或重复说明文档；这些内容会稀释技能目录的信号。

## 生成流程

1. 先判断是否应该触发本技能。若用户只是要完成当前数据处理、分析或转换任务，则先完成任务本身，不要提前进入 skill 生成。只有在用户手动指定生成或保存 skill，或任务已完成且流程经过验证后，才进入后续步骤。
2. 明确具体用例。优先收集用户会怎样调用技能、输入输出文件长什么样、是否需要脚本、是否有字段规则或外部依赖。
3. 规划资源分层。重复且要求稳定的逻辑进入 `scripts/`；长规则进入 `references/`；图标和模板进入 `assets/`。
4. 规范命名。已有业务技能名可保留大小写和下划线，例如 `QC3_NumericDataThresholdCheck`、`Pi_DataSorting`；新通用技能优先使用 lowercase `snake_case` 或 `hyphen-case`；目录名必须等于 `name`。
5. 生成 `SKILL.md`。正文按 `references/piflow_skill_template.md` 的章节顺序组织：功能说明、触发条件、核心功能、处理逻辑、支持的文件格式、使用方法、参数说明、输出参数、示例、输出格式/输出结构、依赖、注意事项。
6. 生成资源目录。只有在 spec 提供或任务需要时写入脚本、引用资料和素材；若有 icon，复制为 `assets/icon.png`。
7. 校验并迭代。运行 `validate_piflow_skill.py`，检查 UTF-8、YAML、参数契约、目录名、资源布局和 UI metadata。
8. 安装后冒烟测试。若该技能需要额外依赖或运行时环境，在环境配置完成后先执行一个最小可运行示例或健康检查脚本，确认关键入口能正常启动并完成一次基础输入输出。
9. 任务完成后再决定是否沉淀。若这次 skill 来自一次真实的数据处理流程，应该在流程成功、结果可信后，再向用户确认是否将该流程保存为 skill；不要在流程未完成前抢先生成。
10. 失败重试与兜底。安装与冒烟测试过程中若失败，先重试再继续；单阶段最多 5 次。若 5 次都失败，停止自动化流程并向用户反馈错误摘要、失败步骤与建议的下一步排查方向。

## Spec 字段

推荐使用 UTF-8 JSON spec：

- `name`：必填，技能目录名和 frontmatter 名称。
- `title`：可选，正文标题和 UI 显示名的候选值。
- `description`：必填，技能能力说明。仅在用户明确要求生成/保存 skill，或任务完成后需要沉淀成功流程时描述 skill 生成能力；不要把宽泛的数据处理诉求直接写成触发词。
- `version`：可选，默认 `1.0.0`。
- `triggers`：可选，触发短语列表，会并入 frontmatter description。触发短语应收敛为“生成 skill”“保存为 skill”“把这次流程沉淀成 skill”等手动或收尾场景，不要把“数据清洗”“数据分析”“处理文件”等本应先直接执行的任务写成优先触发短语。
- `category`：可选，写入 frontmatter、`metadata.category` 和 `skill.json`。
- `tag`：可选，写入 frontmatter 和 `skill.json`，用于 DAG 技能类型。
- `language`：可选，写入 `skill.json`，默认按脚本推断为 `python`。
- `script_path`、`entrypoint`、`command_template`：可选，写入 `skill.json`；缺省时由脚本路径和参数推断。
- `input_params`、`output_params`：PiFlow 参数契约。参数项可包含 `role`。
- `command`：可选，显式命令；缺省时根据 `script.path` 和输入参数生成。
- `script`：可选对象，支持 `path`、`content`、`source`；也可用 `scripts` 列表生成多个脚本。
- `references`：可选列表，支持 `path` + `content` 或 `source`。
- `assets`：可选列表，支持 `path` + `content` 或 `source`；`icon` 会复制为 `assets/icon.png`。
- `dependencies`：可选，正文依赖列表。
- `examples`：可选，正文示例列表。
- `core_features`、`trigger_conditions`、`processing_logic`、`supported_formats`、`output_structure`、`output_examples`：可选，填入通用模板对应章节。
- `body_sections`：可选，自定义正文段落。
- `skill_json`：可选，默认 `true`；设为 `false` 时不生成 `skill.json`。

## 命令

生成技能：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json
```

也可以显式传 `--output-root skills`：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json --output-root skills
```

仅在明确要替换生成目录时使用：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json --overwrite
```

校验技能：

```bash
python scripts/validate_piflow_skill.py skills/<skill-name>
```

## Spec 示例

```json
{
  "name": "clean_example_mapper",
  "title": "Clean Example Mapper",
  "description": "清理文本中的示例片段。",
  "version": "1.0.0",
  "triggers": ["清理示例", "删除示例片段"],
  "category": "mapper",
  "tag": "数据清洗",
  "language": "python",
  "input_params": [
    {"name": "input_path", "role": "input_data", "type": "string", "required": true, "description": "输入 JSON 文件路径"},
    {"name": "output_path", "role": "output_data", "type": "string", "required": true, "description": "输出 JSON 文件路径"}
  ],
  "output_params": [
    {"name": "output_path", "role": "output_data", "type": "json_file", "description": "清理后的 JSON 文件"}
  ],
  "script": {
    "path": "scripts/run_clean_example_mapper.py",
    "content": "import argparse\n\n# TODO: implement operator\n"
  },
  "command_template": ["python", "{script_path}", "--input_path", "{input_path}", "--output_path", "{output_path}"],
  "references": [
    {"path": "references/rules.md", "content": "# 清理规则\n\n- 删除示例片段。"}
  ],
  "dependencies": ["Python 3.x"],
  "examples": [
    {
      "title": "基本调用",
      "command": "python scripts/run_clean_example_mapper.py --input_path input.json --output_path output.json"
    }
  ]
}
```

## 收尾检查

完成前确认：

- `<workspace>/skills/<name>/SKILL.md` 可被 PiFlow 发现；在 deepagent 环境中不要生成到其他根目录。
- `name` 与目录名一致，`description` 包含触发语义。
- 暴露机器可读的 `version`、`category`、`tag`、`input_params` 和 `output_params`。
- 生成的 `skill.json` 包含 `entrypoint`、`script_path`、`command_template` 和带 `role` 的参数元数据。
- 正文足够让另一个 agent 调用或继续实现技能，不依赖隐含上下文。
- 长规则没有塞进正文，而是放入 `references/` 并在正文指明何时读取。
- 脚本、JSON和 Markdown 都能 UTF-8 往返，中文不转义、不乱码。
- 可执行脚本已明确生成、复制或有意省略。
- 技能通过 `validate_piflow_skill.py`。
- 需要运行时依赖的技能，在环境就绪后已完成一次轻量冒烟测试。
- 安装或测试失败时已进行重试；若达到 5 次仍失败，则已向用户反馈明确错误。
- 触发表达已经改写为“仅手动指定或任务完成后沉淀”语义，没有把本技能写成默认优先入口。
- 如果 skill 声明了报告文件或类似结果工件，则失败路径也已实测验证：脚本会优先落盘最小失败摘要和问题清单，再以非零状态码结束，而不是未经兜底直接抛异常退出。

## 新增约束：失败路径可观测

复盘结论：对于会生成报告文件或其他结果工件的 skill，不能只设计成功路径；失败路径也必须可观测、可追溯。入口脚本应优先捕获异常、尽可能落盘最小失败摘要与问题清单，明确失败步骤、原因和上下文，再以非零状态码结束；不要在核心流程中未经兜底地直接抛出异常后退出。

生成此类 skill 时，额外遵守：

- 若 spec 定义了摘要、问题清单、报告或其他结果工件，脚本必须同时实现成功和失败两条输出路径。
- `strict_mode` 或其他失败条件触发时，不应在关键失败产物尚未落盘前直接中断。
- 若只能生成部分结果，也应先写出部分结果，并在失败摘要中标明失败阶段、最后一次错误和未完成项。

## 更有效的自测引导

除 `validate_piflow_skill.py` 外，生成中等及以上复杂度 skill 时，至少执行以下自测：

1. 语法检查：对入口脚本和内部模块运行 `python -m py_compile ...`，先排除最基础的语法问题。
2. 正常样例测试：准备一组最小有效输入，实跑入口脚本，确认关键输出工件全部实际生成，并核对 `summary` 与核心报告内容。
3. 失败样例测试：故意缺少关键输入、配置或依赖，再运行一次，确认脚本返回非零状态码，同时仍能落盘最小失败摘要和问题清单。
4. 输出核对：检查 `skill.json` 中声明的关键输出参数，在正常路径和失败路径下都能找到对应产物，或至少有明确的失败说明。
5. 严格模式核对：若存在 `strict_mode`，必须额外做一次 `strict_mode` 实测，确认它改变的不只是退出码，还包括完整的失败可观测行为。
