# PiFlow Skill 通用模板

生成新技能时优先参照此模板。模板用于保持 `workspace/skills/generated` 内技能的元数据、正文结构和 `skill.json` 结构一致。

路径约定：deepagent 虚拟文件环境以 `workspace` 为根，新技能目录必须位于 `<workspace>/skills/<skill_name>`。生成命令默认使用 `--output-root skills`，不要把技能写入仓库外层或重复嵌套的 workspace 路径。

## SKILL.md Frontmatter

```yaml
---
name: <skill_name>
name_zh: <技能中文名>
description: <说明技能能力，并包含收敛后的触发语义；仅写用户明确指定或任务完成后需要沉淀的触发场景>
version: 1.0.0
category: <业务分类或技能域>
input_params:
  - name: input_path
    role: input_data
    type: string
    required: true
    description: 输入文件路径
output_params:
  - name: output_path
    role: output_data
    type: json_file
    description: 输出文件路径
tag: <DAG 面板技能类型>
---
```

字段规则：

- `name` 必须与目录名一致。
- `name_zh` 必须与中文名一致。
- `description` 必须包含“做什么”和“何时使用”，且“何时使用”应收敛到手动指定或任务完成后的沉淀场景。
- `version` 默认 `1.0.0`。
- `category` 表示技能中心或业务域分类。
- `tag` 表示 DAG 面板中的技能类型，当前入库逻辑会读取为 `skill_type`。
- 参数 `role` 使用 `input_data`、`output_data` 或 `data`。

## SKILL.md Body

推荐章节顺序：

```markdown
# <skill_name> 技能

## 功能说明

用 1 到 2 段说明技能能力、适用对象和输出结果。

## 触发条件

- 当用户明确要求“生成 skill”“保存为 skill”“把这次流程沉淀成 skill”时使用此技能。
- 当某次真实任务已经完成，且需要把已验证成功的处理流程保存为 skill 时使用此技能。
- 不要因为当前任务看起来复杂、可能复用、或暂时能力不足，就默认优先触发此技能。

## 核心功能

- 功能点 1
- 功能点 2
- 功能点 3

## 使用方法

```bash
python scripts/<script>.py --input_path <输入> --output_path <输出>
```

## 参数说明

| 参数 | 类型 | 角色 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| input_path | string | input_data | 是 | - | 输入文件路径 |

## 示例

```bash
python scripts/<script>.py --input_path input.json --output_path output.json
```

## 输出格式

说明输出文件、目录结构或 JSON 结构。

## 注意事项

- UTF-8 读写中文内容。
- 输出目录不存在时应自动创建。
- 图标策略必须明确：要么提供 `assets/icon.png` 作为主图标，要么明确声明使用分类图标作为兜底图标。
```

可按技能复杂度增删章节：

- 数据质控类技能可增加 `处理逻辑`、`支持的文件格式`、`输出示例`。
- 文档解包/打包类技能可增加 `输出结构`。
- 依赖较多的技能可增加 `依赖`。
- 规则较长时将细节放入 `references/`，正文只说明何时读取。

### 失败路径约束（不写到文件，仅作为设计原则）

如果该 skill 会生成报告文件或其他结果工件，则失败路径也必须可观测、可追溯。入口脚本应优先捕获异常并尽可能写出最小失败摘要和问题清单，明确失败步骤、原因和上下文，再返回非零状态码；不要只覆盖成功路径，而在失败时直接抛异常退出。

### 更有效的自测引导（不写到文件，仅作为设计原则）

推荐在技能完成后至少执行以下自测：

- 对入口脚本和内部模块运行 `python -m py_compile ...`，确认没有语法错误。
- 准备一组最小正常输入，实跑入口脚本，确认关键输出工件会被真实写出。
- 再准备一组失败样例，例如缺少核心输入、错误配置或严格模式触发，确认脚本以非零状态码结束，同时能落盘最小失败摘要和问题清单。
- 核对 `skill.json` 中声明的输出参数，在正常和失败两条路径下都具备可观测结果。

### 分层调用建议（不写到文件，仅作为生成器设计原则）

如果技能生成器本身承担“生成内容”和“注册到系统”两类职责，优先拆成两层：

- 生成层：只负责产出技能目录与文件内容，不修改系统全局索引。
- 注册层：只负责把已经生成好的技能注册到列表、图标或其他全局元数据。

在需要兼顾易用性时，可以再保留一个一键封装入口，按“生成层 -> 注册层”的顺序调用。这样更适合 agent 在不同场景下做：

- 先生成草稿，再审核，再注册
- 只补注册
- 只重生成内容但不触碰全局状态

## skill.json

```json
{
  "name": "<skill_name>",
  "version": "1.0.0",
  "description": "<技能描述>",
  "language": "python",
  "script_path": "scripts/run_<skill_name>.py",
  "entrypoint": "python scripts/run_<skill_name>.py",
  "input_params": [
    {
      "name": "input_path",
      "role": "input_data",
      "type": "string",
      "required": true,
      "description": "输入文件路径"
    }
  ],
  "output_params": [
    {
      "name": "output_path",
      "role": "output_data",
      "type": "json_file",
      "description": "输出文件路径"
    }
  ],
  "command_template": [
    "python",
    "{script_path}",
    "--input_path",
    "{input_path}",
    "--output_path",
    "{output_path}"
  ]
}
```

`skill.json` 应与 `SKILL.md` 中的 `name`、`version`、参数名称和参数角色保持一致。生成后目录应位于 `<workspace>/skills/<skill_name>`，并包含 `SKILL.md` 与 `skill.json`。
