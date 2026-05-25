---
name: piflow-skill-generator
description: |
  PiFlow 技能生成器。根据当前 workspace/skills 的本地约定和 references/piflow_skill_template.md 通用模板创建、更新或校验 PiFlow-compatible skill，包括 UTF-8 编码的 SKILL.md、DAG 可读的 input_params/output_params、version/category/tag 元数据、skill.json、scripts/references/assets 资源目录、可选 agents/openai.yaml，以及本地校验脚本。用户提到创建技能、生成 skill、封装算子、补齐技能元数据、按模板生成技能、实现技能闭包或校验技能格式时使用此 skill。
name_zh: PiFlow 技能生成器
version: 1.1.1
category: skill_generation
tag: 技能生成
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
---

# PiFlow Skill Generator

## 核心规则

除去对运行/测试时的产物进行分析，其他工作应尽量提前计划和生成，避免在安装或测试阶段才发现文档不完整、脚本缺失或资源错误。技能生成器的目标是一次性生成一个完整、可靠、符合约定的技能目录，能直接被 PiFlow 识别和使用。

生成能被 PiFlow 理解的技能目录。所有文本文件必须以 UTF-8 读写，尤其是中文内容；Python 读写文件时显式使用 `encoding="utf-8"`，JSON/YAML 输出使用 `ensure_ascii=False`。

按库内技能的粒度控制内容：`SKILL.md` 只放触发、流程和必要契约；可执行逻辑放 `scripts/`；较长规则、字段说明和领域资料放 `references/`；模板、图标、示例素材放 `assets/`。

生成正文时优先参照 `references/piflow_skill_template.md`。当 spec 中提供 `core_features`、`trigger_conditions`、`processing_logic`、`supported_formats`、`output_structure`、`output_examples` 等字段时，将它们填入模板对应章节。

本技能必须能在没有其他技能辅助的环境中独立生成可靠技能：只依赖当前技能目录内的 `SKILL.md`、`references/piflow_skill_template.md`、`scripts/generate_piflow_skill.py` 和 `scripts/validate_piflow_skill.py`。生成时不要假设另一个 skill 会补全文档、脚本或元数据。

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
├── agents/
│   └── openai.yaml        # 可选，UI 元数据
├── scripts/               # 可选，稳定可执行逻辑
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
- `tag`：面向 DAG 面板的技能类型；当前入库逻辑会读取 `tag` 作为 `skill_type`。
- `input_params`：PiFlow DAG 面板读取的输入参数列表，必须保留。
- `output_params`：PiFlow DAG 面板读取的输出参数列表，必须保留。
- `allowed-tools`、`compatibility`、`license`、`metadata`：仅在确实需要时添加。

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

### agents/openai.yaml

当需要技能列表、快捷入口或 UI chip 时生成。字符串必须加引号，`default_prompt` 必须明确包含 `$skill-name`。

```yaml
interface:
  display_name: "技能显示名"
  short_description: "用于 UI 扫描的短说明"
  icon_small: "./assets/icon.png"
  icon_large: "./assets/icon.png"
  default_prompt: "Use $skill-name to ..."
```

只在用户或 spec 明确提供时写入 `brand_color`、`dependencies` 或 `policy` 等扩展字段。

### Bundled Resources

- `scripts/`：放确定性脚本、算子封装、批处理逻辑。脚本应可通过 `python scripts/<name>.py ...` 调用，并使用 UTF-8 读写。
- `references/`：放长规则、字段字典、API 说明、数据 schema、复杂示例。正文中必须说明何时读取哪个引用文件。
- `assets/`：放图标、模板、示例素材、字体或输出需要复制的资源。PiFlow 技能中心优先寻找 `assets/icon.png`。

不要生成与执行无关的 `README.md`、安装指南、变更日志或重复说明文档；这些内容会稀释技能目录的信号。

## 生成流程

1. 明确具体用例。优先收集用户会怎样调用技能、输入输出文件长什么样、是否需要脚本、是否有字段规则或外部依赖。
2. 规划资源分层。重复且要求稳定的逻辑进入 `scripts/`；长规则进入 `references/`；图标和模板进入 `assets/`。
3. 规范命名。已有业务技能名可保留大小写和下划线，例如 `QC3_NumericDataThresholdCheck`、`Pi_DataSorting`；新通用技能优先使用 lowercase `snake_case` 或 `hyphen-case`；目录名必须等于 `name`。
4. 生成 `SKILL.md`。正文按 `references/piflow_skill_template.md` 的章节顺序组织：功能说明、触发条件、核心功能、处理逻辑、支持的文件格式、使用方法、参数说明、输出参数、示例、输出格式/输出结构、依赖、注意事项。
5. 生成资源目录。只有在 spec 提供或任务需要时写入脚本、引用资料和素材；若有 icon，复制为 `assets/icon.png`。
6. 生成 `agents/openai.yaml`。当 spec 设置 `agents_openai: true` 或提供 `agents_openai` 对象时生成，并保证 UI 文案来自技能本身。
7. 校验并迭代。运行 `validate_piflow_skill.py`，检查 UTF-8、YAML、参数契约、目录名、资源布局和 UI metadata。
8. 安装后冒烟测试。若该技能需要额外依赖或运行时环境，在环境配置完成后先执行一个最小可运行示例或健康检查脚本，确认关键入口能正常启动并完成一次基础输入输出。
9. 失败重试与兜底。安装与冒烟测试过程中若失败，先重试再继续；单阶段最多 5 次。若 5 次都失败，停止自动化流程并向用户反馈错误摘要、失败步骤与建议的下一步排查方向。

## Spec 字段

推荐使用 UTF-8 JSON spec：

- `name`：必填，技能目录名和 frontmatter 名称。
- `title`：可选，正文标题和 UI 显示名的候选值。
- `description`：必填，技能能力说明。
- `version`：可选，默认 `1.0.0`。
- `triggers`：可选，触发短语列表，会并入 frontmatter description。
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
- `agents_openai`：可选，布尔值或对象；对象可提供 `display_name`、`short_description`、`default_prompt`、`brand_color`。
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
  ],
  "agents_openai": true
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
- 脚本、JSON、YAML 和 Markdown 都能 UTF-8 往返，中文不转义、不乱码。
- 可执行脚本已明确生成、复制或有意省略。
- 若生成 `agents/openai.yaml`，其中 `default_prompt` 包含 `$skill-name`。
- 技能通过 `validate_piflow_skill.py`。
- 需要运行时依赖的技能，在环境就绪后已完成一次轻量冒烟测试。
- 安装或测试失败时已进行重试；若达到 5 次仍失败，则已向用户反馈明确错误。
