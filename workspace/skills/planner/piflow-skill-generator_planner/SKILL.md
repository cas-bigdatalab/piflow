---
name: piflow-skill-generator_planner
description: |
  PiFlow 技能生成器。当用户完成了一次完整并成功的数据处理任务时调用，根据当前 skills/generated 的本地约定和 references/piflow_skill_template.md 通用模板创建、更新或校验 PiFlow-compatible skill，包括 UTF-8 编码的 SKILL.md、DAG 可读的 input_params/output_params、version/tag 元数据、skill.json、scripts/references/assets 资源目录，以及本地校验脚本。仅在用户明确要求生成或保存 skill，或某次数据处理任务已经完成并需要把已验证成功的操作流程沉淀为 skill 时使用；默认不要因为“可能需要 skill”或“当前能力不足”而优先触发此 skill。
name_zh: PiFlow 算子生成器_planner
version: 1.1.2
allowed-tools:
  - process

input_params:
  - name: spec_path
    type: string
    required: false
    description: 技能规格 JSON 文件路径，必须使用 UTF-8 编码；与 flow_path 二选一

  - name: output_root
    type: string
    required: false
    default: skills/generated
    description: 输出根目录；deepagent 虚拟文件环境默认写入 skills/generated（相对于 workspace 根）

  - name: overwrite
    type: bool
    required: false
    default: false
    description: 是否覆盖已存在的技能目录

  - name: thread_id
    type: string
    required: false
    description: 当前会话 ID；提供后记录生成 skill 供前端预览

  - name: flow_path
    type: string
    required: false
    description: 已验证成功的流程摘要 JSON 路径；与 spec_path 二选一

  - name: restored_spec_out
    type: string
    required: false
    description: 使用 flow_path 时恢复出的 spec 草稿输出路径

  - name: rewrite_followup_hint
    type: string
    required: false
    default: ""
    description: 可选提示语；当 skill 生成完成后，如用户随后给出新的流程，可提示是否进入生成器内部改写链路继续改写

output_params:
  - name: skill_dir
    type: directory
    description: 生成后的技能目录

  - name: skill_md
    type: markdown_file
    description: 生成后的 SKILL.md

  - name: rewrite_followup_suggestion
    type: json_file
    description: 生成完成后的改写 follow-up 建议信息
tag: 算子生成
---

# PiFlow Skill Generator Planner

## 核心规则

本技能是一个**模板驱动的 PiFlow skill 生成器**。它的职责不是找一个相似 skill 来改改，而是基于统一模板，把用户明确提供的信息、已经验证成功的流程、已有脚本和必要资源，整理成一个结构清晰、参数契约稳定、可被 PiFlow 直接识别的技能目录。

生成目标始终是一次性产出完整、可靠、符合约定的 skill 目录，包括 UTF-8 编码的 `SKILL.md`、DAG 可读的 `input_params` / `output_params`、`skill.json`、`scripts/`、`references/`、`assets/`，以及必要的校验与注册结果。**每个生成的 skill 必须包含一个可执行 Python 入口脚本**：优先复用已验证实现；没有现成实现时也必须生成 `scripts/run_<skill_name>.py`，使其可解析参数并输出结构化运行结果，禁止只生成元数据文件。但它不是默认优先入口；只有在用户明确要“生成/保存为 skill”，或某个流程已经真实跑通并值得沉淀时，才进入这条链路。

所有文本文件必须使用 UTF-8 读写，尤其是中文内容；Python 读写文件时显式使用 `encoding="utf-8"`，JSON 输出使用 `ensure_ascii=False`。

目录内容按职责分层：
- `SKILL.md`：只放触发条件、处理流程、参数契约和必要说明；
- `scripts/`：放稳定、可执行、可测试的入口脚本或处理逻辑；
- `references/`：放长规则、字段字典、复杂 schema、补充说明；
- `assets/`：放图标、模板、示例素材或需要随技能一起交付的资源。

本技能的实现指引遵循同一条主线：**模板优先，参考次之，禁止默认整体仿写**。
- 先以 `references/piflow_skill_template.md` 作为 `SKILL.md`、`skill.json`、参数组织方式、脚本入口形状和资源分层的统一骨架；
- 再把用户确认的信息、成功流程、已有脚本、现有 skill 中真正有用的规则和参数事实，填回模板对应位置；
-当 spec 中提供 `core_features`、`trigger_conditions`、`processing_logic`、`supported_formats`、`output_structure`、`output_examples` 等字段时，将它们填入模板对应章节

因此，无论是直接生成、基于已验证流程生成，还是生成后的再次改写，最终输出都必须回到模板定义的结构，而不是回到某个历史 skill 的结构。

本技能必须能在没有其他技能辅助的环境中独立生成可靠技能：只依赖当前技能目录内的 `SKILL.md`、`references/piflow_skill_template.md`、`scripts/generate_piflow_skill.py`、`scripts/generate_skill_files.py`、`scripts/register_skill_artifacts.py`、`scripts/rewrite_piflow_skill.py` 和 `scripts/validate_piflow_skill.py`。生成时不要假设另一个 skill 会补全文档、脚本或元数据。本技能负责 skill 化与沉淀，不负责代替用户完成所有真实处理任务本身。

本技能支持两种使用方式：

1. 直接生成
   当用户明确要求“生成 skill”“保存为 skill”“封装为 skill”“创建自定义技能”时，根据已确认的规格生成 skill。

2. 基于已验证流程生成或改写
   当用户提供已验证成功的流程、脚本或输入输出约定时，优先复用这些事实生成或最小改写 skill；改写时默认保留原 skill 名称和目录位置，避免生成含义重复的新 skill。

在涉及安装、环境准备或可执行脚本验证时，优先完成最小必要依赖，再运行一个简单冒烟测试确认关键入口可执行、基础参数可解析、输出路径可写。若安装或测试失败，允许自动重试，单个阶段最多重试 5 次；若 5 次后仍失败，停止流程并把失败原因、失败步骤和最后一次错误返回给用户。

安装依赖或配置前置环境时，若不明确安装的流程或操作，需要调用网络工具获取安装指南或官方文档，或者直接调用搜索查询安装步骤，不要假设已经知道如何安装或配置。

## 路径规则

deepagent 的虚拟文件环境以 `workspace` 为根。生成的技能必须放在 `skills/generated/<skill-name>`（相对于 workspace 根），这样 PiFlow 才能发现。

- 默认 `output_root` 使用 `skills/generated`，表示 `<workspace>/skills/generated`。
- `write_file`/`read_file` 等工具调用时使用相对于 workspace 根的虚拟路径（如 `skills/generated/<skill_name>/`），**不要带 `workspace/` 前缀**。
- Shell 命令中使用 `--output-root skills/generated`。
- 如果用户传入旧路径 `workspace/skills` 或 `flow-deepagents/workspace/skills`，脚本会归一化为当前 deepagent workspace 下的 `skills/generated`。
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
    └── icon.png           # 必须选定的主图标；若没有自定义图标，需明确兜底到分类图标
```

### SKILL.md

`SKILL.md` 由 YAML frontmatter 和 Markdown body 组成。

- `name`：必须与目录名完全一致。
- `description`：主要触发入口。必须同时说明技能做什么、用户在什么表达或场景下应触发。触发信息写在这里，不要只写在正文。
- `version`：技能版本，默认 `1.0.0`。
- `input_params`：PiFlow DAG 面板读取的输入参数列表，必须保留。
- `output_params`：PiFlow DAG 面板读取的输出参数列表，必须保留。
- `allowed-tools`、`compatibility`、`license`、`metadata`：仅在确实需要时添加。
- `tag`：面向 DAG 面板的技能类型；当前入库逻辑会读取 `tag` 作为 `skill_type`。

参数项使用：

```yaml
- name: input_path
  type: string
  required: true
  default: optional-default
  description: 输入文件路径
```

`SKILL.md` frontmatter 的参数项禁止包含 `role`。`role` 是 DAG 专用元数据，只应写入 `skill.json`；生成器会依据参数的 `type`、`name` 和 `description` 在 JSON 中推断 `input_data`、`output_data` 或 `data`。

### skill.json

当 `skill_json` 未显式设为 `false` 时生成。该文件用于 DAG 执行链路和画板解析，包含：

- `name`、`version`、`description`
- `language`
- `script_path`
- `entrypoint`
- `input_params`、`output_params`，其中参数保留 `role`
- `command_template`
- 可选 `tag`


只在用户或 spec 明确提供时写入 `dependencies` 或 `policy` 等扩展字段。

### Bundled Resources

- `scripts/`：每个 skill 都必须包含一个确定性、可执行的 Python 入口脚本。优先复用已验证逻辑；若没有现成逻辑，生成 `scripts/run_<skill_name>.py`，它必须接受声明的输入参数并输出 JSON 运行摘要。脚本应可通过 `python scripts/<name>.py ...` 调用，并使用 UTF-8 读写。
- `references/`：放长规则、字段字典、API 说明、数据 schema、复杂示例。正文中必须说明何时读取哪个引用文件。
- `assets/`：放图标、模板、示例素材、字体或输出需要复制的资源。每个 skill 在生成阶段都应明确一个主图标方案：优先提供 `assets/icon.png`；若暂时没有自定义图标，也必须在设计与交付时明确兜底使用对应分类图标，不要让图标策略处于未定义状态。

不要生成与执行无关的 `README.md`、安装指南、变更日志或重复说明文档；这些内容会稀释技能目录的信号。

## 生成流程

### A. 手动生成链路

1. 先判断用户是否明确要求生成或保存 skill。若是，则直接进入本链路。
2. 明确具体用例。优先收集用户会怎样调用技能、输入输出文件长什么样、是否需要脚本、是否有字段规则或外部依赖。
3. 规划资源分层。重复且要求稳定的逻辑进入 `scripts/`；长规则进入 `references/`；图标和模板素材进入 `assets/`。这一阶段同时确定图标策略：选一个主图标来源，并明确一个兜底图标。
4. 规范命名。已有业务技能名可保留大小写和下划线，例如 `QC3_NumericDataThresholdCheck`、`Pi_DataSorting`；新通用技能优先使用 lowercase `snake_case` 或 `hyphen-case`；目录名必须等于 `name`。
5. 先按 `references/piflow_skill_template.md` 搭骨架，再填内容。正文章节顺序、frontmatter 结构、`skill.json` 参数契约、脚本入口和资源目录都应先服从模板；随后再把用户确认的信息、成功流程信息、脚本信息和必要规则填入对应章节。不要先挑一个相似 skill 作为底稿整体改写。
6. 生成资源目录。必须写入 `scripts/run_<skill_name>.py` 或用户提供的等价 Python 脚本；脚本必须与 `skill.json` 的 `script_path`、`entrypoint` 和 `command_template` 一致。只有引用资料和素材可按需省略；图标必须有明确结论：若 spec 提供 `icon`，复制为 `assets/icon.png` 作为主图标；若未提供自定义图标，则记录并验证可兜底到分类图标。
7. 校验并迭代。运行 `validate_piflow_skill.py`，检查 UTF-8、YAML、参数契约、目录名、资源布局和 UI metadata。
8. 安装后冒烟测试。若该技能需要额外依赖或运行时环境，在环境配置完成后先执行一个最小可运行示例或健康检查脚本，确认关键入口能正常启动并完成一次基础输入输出。
9. 失败重试与兜底。安装与冒烟测试过程中若失败，先重试再继续；单阶段最多 5 次。若 5 次都失败，停止自动化流程并把失败原因、失败步骤和最后一次错误返回给用户。

### B. 基于已验证流程生成或改写

1. 读取用户提供的成功流程、脚本、样例输入输出和验证结果。
2. 优先将已有事实恢复为 spec 草稿；仅补问无法从现有材料确定的字段。
3. 使用与直接生成相同的生成、校验、注册和冒烟测试流程。
4. 若目标 skill 已存在，则复用其名称和目录，通过 `overwrite` 做最小改写。

## 三层调用模型

当前实现按职责拆成三层，并保留一个一键封装入口：

1. 生成层
   负责把 spec 落成技能目录本身，包括 `SKILL.md`、`skill.json`、`scripts/`、`references/`、`assets/` 等内容。
   对应脚本：`scripts/generate_skill_files.py`

2. 注册层
   负责把已生成好的技能接入 PiFlow 可见索引，包括更新 `docs/skill分类.txt`，以及同步 `storage/skills` 下的技能图标与分类图标。
   对应脚本：`scripts/register_skill_artifacts.py`


3. 一键封装层
   按顺序调用“生成层 -> 注册层”，适合默认使用。
   对应脚本：`scripts/generate_piflow_skill.py`

### 调用建议

- 当你需要“先生成草稿、再人工检查、最后再发布/注册”时：
  先调用生成层，再调用 `validate_piflow_skill.py --mode files-only`，确认通过后再调用注册层。

- 当你需要“一次性生成并接入系统可见列表”时：
  直接调用一键封装层。

- 当你只是想更新技能正文、脚本、资源，但暂时不希望污染全局分类列表或图标存储时：
  只调用生成层，不调用注册层。

- 当技能目录已经存在，只是因为分类列表或图标丢失，需要补注册时：
  只调用注册层。

- 当用户提供一次成功的真实处理流程时：
  优先恢复流程草稿 spec，再补缺失字段，然后根据是否需要立即可见，选择“只生成”或“一键生成并注册”。

- 当用户为已生成 skill 提供新的流程指引时：
  保留原 skill 名称并使用 `overwrite` 重建，避免从零生成同义 skill。

## Spec 字段

推荐使用 UTF-8 JSON spec：

- `name`：必填，技能目录名和 frontmatter 名称。
- `title`：可选，正文标题和 UI 显示名的候选值。
- `description`：必填，技能能力说明。仅在用户明确要求生成/保存 skill，或任务完成后需要沉淀成功流程时描述 skill 生成能力；不要把宽泛的数据处理诉求直接写成触发词。
- `description`：必填，技能能力说明。描述用户如何显式触发此 skill，不要把宽泛的数据处理诉求写成默认优先入口。
- `version`：可选，默认 `1.0.0`。
- `triggers`：可选，触发短语列表，会并入 frontmatter description。触发短语应收敛为“生成 skill”“保存为 skill”“把这次流程沉淀成 skill”等手动或收尾场景，不要把“数据清洗”“数据分析”“处理文件”等本应先直接执行的任务写成优先触发短语。
- `tag`：可选，写入 frontmatter 和 `skill.json`，用于 DAG 技能类型。
- `language`：可选，写入 `skill.json`，默认按脚本推断为 `python`。
- `script_path`、`entrypoint`、`command_template`：必填，写入 `skill.json`；必须指向 skill 内存在的 Python 脚本，并与输入参数一致。
- `input_params`、`output_params`：PiFlow 参数契约。参数项可包含 `role`。
- `input_params`、`output_params` 在 `SKILL.md` frontmatter 和 `skill.json` 中都必须是“参数对象数组”，禁止写成 `{ params: {...} }`、`{input_path: {...}}` 或任何对象映射形状；每个参数必须独立占一个数组元素。
- `command`：可选，显式命令；缺省时根据 `script.path` 和输入参数生成。
- `script`：必填对象，支持 `path`、`content`、`source`；也可用 `scripts` 列表生成多个脚本。未提供时生成器默认创建 `scripts/run_<name>.py`。若来自成功流程或旧实现，优先恢复其可执行事实，但最终脚本路径、入口命名、参数契约和目录组织仍要服从模板，而不是服从原始样例的偶然结构。
- `script` / `scripts`：优先从成功运行的脚本、流程文件或实现产物恢复，再将这些内容回填进模板约定的目录结构、参数契约和资源分层；不要因为参考了旧脚本或旧 skill，就偏离模板去整体复刻旧实现。
- `references`：可选列表，支持 `path` + `content` 或 `source`。
- `assets`：可选列表，支持 `path` + `content` 或 `source`；`icon` 会复制为 `assets/icon.png`。无论是否提供自定义 `icon`，都必须在生成时明确一个兜底图标方案，默认可回退到分类图标。
- `dependencies`：可选，正文依赖列表。
- `examples`：可选，正文示例列表。
- `core_features`、`trigger_conditions`、`processing_logic`、`supported_formats`、`output_structure`、`output_examples`：可选，填入通用模板对应章节。
- `body_sections`：可选，自定义正文段落。
- `skill_json`：可选，默认 `true`；设为 `false` 时不生成 `skill.json`。
- `metadata`：可选；可用于记录流程来源、验证摘要和沉淀时间。
- `rewrite_followup_hint`：可选；用于在生成结果中覆盖默认的改写 follow-up 提示语。

## 命令

一键生成并注册技能：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json --thread-id <thread_id>
```

前端预览生成结果时，传入当前 `thread_id`；生成器会将会话 ID、skill 名称和 workspace 相对目录写入 `generating_skills`。同一会话再次生成时会更新该记录。

也可以显式传 `--output-root skills`：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json --output-root skills
```

如果已有一次已经跑通的成功流程，也可以直接传流程摘要：

```bash
python scripts/generate_piflow_skill.py --flow path/to/flow-summary.json --restored-spec-out path/to/restored-spec.json --output-root skills
```

若 skill 已生成完成，且用户随后提供了新的流程作为改写指引：

```bash
python scripts/rewrite_piflow_skill.py --skill-dir skills/<skill-name> --flow path/to/new-flow-summary.json --restored-spec-out artifacts/rewrite-spec.json
```

改写链路的依赖说明与边界约束见：

```text
references/rewrite_followup_internal.md
```

仅在明确要替换生成目录时使用：

```bash
python scripts/generate_piflow_skill.py --spec path/to/spec.json --overwrite
```

仅生成技能文件，不注册列表和图标：

```bash
python scripts/generate_skill_files.py --spec path/to/spec.json --output-root skills
```

若只想把成功流程恢复为 draft spec 再人工检查：

```bash
python scripts/restore_flow_to_spec.py --flow path/to/flow-summary.json --output path/to/restored-spec.json
```

若想直接从成功流程生成技能文件而不注册：

```bash
python scripts/generate_skill_files.py --flow path/to/flow-summary.json --restored-spec-out path/to/restored-spec.json --output-root skills
```

仅注册已有技能目录的列表和图标：

```bash
python scripts/register_skill_artifacts.py --spec path/to/spec.json --skill-dir skills/<skill-name>
```

若当前只有成功流程摘要，也可以直接在注册时恢复 spec：

```bash
python scripts/register_skill_artifacts.py --flow path/to/flow-summary.json --restored-spec-out path/to/restored-spec.json --skill-dir skills/<skill-name>
```

校验技能：

```bash
python scripts/validate_piflow_skill.py skills/<skill-name>
```

仅校验生成层产物：

```bash
python scripts/validate_piflow_skill.py skills/<skill-name> --mode files-only
```

## Spec 示例

```json
{
  "name": "clean_example_transformer",
  "title": "Clean Example Transformer",
  "description": "清理文本中的示例片段。",
  "version": "1.0.0",
  "triggers": ["清理示例", "删除示例片段"],
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
    "path": "scripts/run_clean_example_transformer.py",
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
      "command": "python scripts/run_clean_example_transformer.py --input_path input.json --output_path output.json"
    }
  ]
}
```

## 必要的测试

完成前确认：

- `<workspace>/skills/<name>/SKILL.md` 可被 PiFlow 发现；在 deepagent 环境中不要生成到其他根目录。
- `name` 与目录名一致，`description` 包含触发语义。
- 暴露机器可读的 `version`、`tag`、`input_params` 和 `output_params`。
- 生成的 `skill.json` 包含 `entrypoint`、`script_path`、`command_template` 和带 `role` 的参数元数据。
- 正文足够让另一个 agent 调用或继续实现技能，不依赖隐含上下文。
- 长规则没有塞进正文，而是放入 `references/` 并在正文指明何时读取。
- 脚本、JSON 和 Markdown 都能 UTF-8 往返，中文不转义、不乱码。
- 可执行 Python 脚本已生成或复制，且与 `skill.json` 的入口元数据一致；禁止省略。
- 输出结构以 `references/piflow_skill_template.md` 为主骨架；即使引用了旧脚本、旧 skill 或成功流程，也没有退化为对相似 skill 的整体复刻。
- 技能通过 `validate_piflow_skill.py`。
- 需要运行时依赖的技能，已在环境就绪后做过最小冒烟测试。
- 安装或测试失败时已进行重试；若达到 5 次仍失败，则已向用户反馈明确错误。
- 触发表达已经收敛为“仅手动指定或任务完成后沉淀”，没有把本技能写成默认优先入口。
- 如果 skill 生成后用户又提供了新的成功流程，已考虑是否提示进入内部改写链路继续做最小改写。
- 如果 skill 声明了报告文件或类似结果工件，则失败路径也已实测验证：脚本会优先落盘最小失败摘要和问题清单，再以非零状态码结束，而不是未经兜底直接抛异常退出。

## 失败路径可观测性约束

复盘结论：对于会生成报告文件或其他结果工件的 skill，不能只设计成功路径；失败路径也必须可观测、可追溯。入口脚本应优先捕获异常、尽可能落盘最小失败摘要与问题清单，明确失败步骤、原因和上下文，再以非零状态码结束；不要在核心流程中未经兜底地直接抛出异常后退出。

生成此类 skill 时，额外遵守：

- 若 spec 定义了摘要、问题清单、报告或其他结果工件，脚本必须同时实现成功和失败两条输出路径。
- `strict_mode` 或其他失败条件触发时，不应在关键失败产物尚未落盘前直接中断。
- 若只能生成部分结果，也应先写出部分结果，并在失败摘要中标明失败阶段、最后一次错误和未完成项。
> 不要记录以下内容（这些会变成长期存在的自我约束，并在环境变化后反过来带来影响）：
>>  环境相关故障：缺失二进制文件、全新安装错误、迁移后路径不匹配、command not found、未配置凭据、未安装软件包等。用户可以修复这些问题，它们不是持久规则。
>>  关于工具或功能的负面断言：如“浏览器工具无法工作”、“X 工具已损坏”、“远程资源不包含 Y”等。这些会固化成长期拒绝理由，即使实际问题早已被修复。
>>  会话中已经解决的临时错误。如果重试后成功了，应记录重试模式，而不是原始失败。
>>  一次性任务叙述。用户要求“总结今天的市场”或“分析这个 PR”，并不构成一个值得创建技能的工作类别。

## 自测引导

除 `validate_piflow_skill.py` 外，生成中等及以上复杂度 skill 时，至少执行以下自测：

1. 语法检查：对入口脚本和内部模块运行 `python -m py_compile ...`，先排除最基础的语法问题。
2. 正常样例测试：准备一组最小有效输入，实跑入口脚本，确认关键输出工件全部实际生成，并核对 `summary` 与核心报告内容。
3. 失败样例测试：故意缺少关键输入、配置或依赖，再运行一次，确认脚本返回非零状态码，同时仍能落盘最小失败摘要和问题清单。
4. 输出核对：检查 `skill.json` 中声明的关键输出参数，在正常路径和失败路径下都能找到对应产物，或至少有明确的失败说明。
5. 严格模式核对：若存在 `strict_mode`，必须额外做一次 `strict_mode` 实测，确认它改变的不只是退出码，还包括完整的失败可观测行为。
