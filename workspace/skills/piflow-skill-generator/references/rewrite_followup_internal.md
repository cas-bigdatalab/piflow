# 生成后改写内部参考

本文档描述 `piflow-skill-generator` 在“skill 已生成后，用户又提供了新的成功流程”场景下的内部改写机制。该机制是生成器的内部参考能力，不作为独立对外 skill 发布。

## 适用场景

- 一个 skill 已经生成完成，并通过了基础校验。
- 用户随后又给出了新的成功流程、更新后的输入输出约定，或新的脚本实现。
- 目标不是重新创建一个同义 skill，而是在保留原 skill 名称的前提下，对刚生成的 skill 做一次最小重写。

## 触发方式

主 skill 可在生成完成后向用户询问：

- “是否要以这次新的流程作为指引，对刚生成的 skill 再做一次改写？”

若用户确认，则进入内部改写链路，而不是转到新的公开 skill。

## 依赖关系

当前内部改写链路由以下文件组成：

- `scripts/rewrite_piflow_skill.py`
  - 内部改写入口。
- `scripts/generate_piflow_skill.py`
  - 提供共享基础能力，包括：
  - `read_spec_input`
  - `resolve_output_root`
  - `resolve_source_path`
  - `restore_spec_from_flow`
  - `read_text`
  - `write_text`
  - `generate`
- `scripts/validate_piflow_skill.py`
  - 用于改写后的 files-only 或完整校验。
- `scripts/test_rewrite_flow_spec.py`
  - 用于最小单测覆盖。

依赖方向应保持单向：

- `rewrite_piflow_skill.py` 依赖 `generate_piflow_skill.py`
- `test_rewrite_flow_spec.py` 依赖 `rewrite_piflow_skill.py`
- 主 `SKILL.md` 只引用本参考文档，不反向依赖任何独立改写 skill

不要把 `rewrite_piflow_skill.py` 设计成反向调用主 skill 文档或另一个“改写 skill”的入口，否则会形成职责重复。

## 最小行为

内部改写机制当前只提供“最小重写”能力：

1. 读取已有 skill 目录。
2. 解析用户提供的新流程摘要或新的 rewrite spec。
3. 强制复用原 skill 名称。
4. 以 `overwrite=True` 调用主生成器的生成与注册逻辑。
5. 输出改写后的 skill 目录和恢复出的 rewrite spec。

这意味着当前实现并不是增量 patch 编辑器，而是：

- “恢复 rewrite spec”
- “复用原名称”
- “整目录重建并覆盖”

## 约束

- 这是生成器的内部参考能力，不应再暴露为独立 skill。
- 改写链路默认复用原 skill 名称和目录位置。
- 若用户只是补充分类、图标或注册信息，优先考虑主生成器现有注册链路，而不是走内部改写。
- 若未来需要更细粒度的字段级 patch，再单独扩展，不要直接把当前最小实现伪装成增量编辑器。

## 建议调用顺序

1. 主生成器完成首次 skill 生成。
2. 用户给出新的成功流程或新的脚本指引。
3. 生成器询问是否按该流程继续改写。
4. 若用户同意，调用：

```bash
python scripts/rewrite_piflow_skill.py --skill-dir skills/<skill-name> --flow path/to/new-flow-summary.json --restored-spec-out workspace/artifacts/rewrite-spec.json
```

5. 改写完成后，执行：

```bash
python scripts/validate_piflow_skill.py skills/<skill-name> --mode files-only
```

如需更严格验证，再执行完整校验或真实样例自测。
