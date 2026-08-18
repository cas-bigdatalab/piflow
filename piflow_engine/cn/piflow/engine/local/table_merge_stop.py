"""多路表格汇聚算子。

跨域调度里最常见的一步是「把几个数据中心各自读来的表拼成一张」，此前算子库里
没有能接多路上游的算子，规划器只能退化成占位算子。这个算子填的就是这个缺口。

和 TextFileMergeStop 的区别：那个是两路纯文本首尾相接，这个认表结构 —— 列名
对齐、按键关联、列名冲突显式加后缀，路数也不限于两路。

只依赖标准库 csv：engine/local 下的算子都是这个路数，装了最小依赖的执行节点
也能跑起来。
"""

from __future__ import annotations

import csv
import re
import uuid
from pathlib import Path
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name


OUTPUT_PORT = "output"

# 对外声明的入口端口数。端口名由 DAG 的连线决定，perform 里读的是实际连进来的
# 那些，所以这个上限只影响规划器「一个节点最多能汇聚几路」的判断；再多就该拆成
# 多级汇聚了，一个节点里塞十几路既不好读也不好排障。
MAX_INPUT_PORTS = 8
INPUT_PORTS = [f"input_{i}" for i in range(1, MAX_INPUT_PORTS + 1)]

MODE_CONCAT = "concat"
MODE_JOIN = "join"
JOIN_TYPES = ("inner", "left", "outer")


class TableMergeStop(ConfigurableStop):
    author_email = ""
    description = (
        "Merge multiple tabular (CSV/TSV) inputs into one table, "
        "either by stacking rows (concat) or by joining on key columns (join)."
    )
    inport_list = list(INPUT_PORTS)
    outport_list = [OUTPUT_PORT]

    def __init__(self) -> None:
        super().__init__()
        self.mode = MODE_CONCAT
        self.join_keys: list[str] = []
        self.join_type = "inner"
        self.output_file_name = "merged.csv"
        self.delimiter = ","
        self.encoding = "utf-8"
        self.source_column = ""
        self._workspace_root: Path | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.mode = _text(properties.get("mode"), MODE_CONCAT).lower()
        if self.mode not in (MODE_CONCAT, MODE_JOIN):
            raise ValueError(
                f"table merge mode must be one of {(MODE_CONCAT, MODE_JOIN)}, got {self.mode!r}"
            )

        self.join_keys = [
            part.strip()
            for part in _text(properties.get("join_keys"), "").split(",")
            if part.strip()
        ]
        self.join_type = _text(properties.get("join_type"), "inner").lower()
        if self.join_type not in JOIN_TYPES:
            raise ValueError(
                f"table merge join_type must be one of {JOIN_TYPES}, got {self.join_type!r}"
            )

        if self.mode == MODE_JOIN and not self.join_keys:
            raise ValueError("table merge mode 'join' requires property 'join_keys'")

        self.output_file_name = (
            Path(_text(properties.get("output_file_name"), "merged.csv")).name
            or "merged.csv"
        )
        # 分隔符允许写成 \t，YAML/JSON 里手写制表符太容易被编辑器吃掉
        self.delimiter = _text(properties.get("delimiter"), ",").replace("\\t", "\t")
        if len(self.delimiter) != 1:
            raise ValueError(
                f"table merge delimiter must be a single character, got {self.delimiter!r}"
            )
        self.encoding = _text(properties.get("encoding"), "utf-8")
        self.source_column = _text(properties.get("source_column"), "")

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        sources = self._read_sources(inputs)
        if self.mode == MODE_JOIN:
            columns, rows = self._join(sources)
        else:
            columns, rows = self._concat(sources)

        output_path = self._prepare_output_path(ctx)
        with output_path.open("w", encoding=self.encoding, newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=columns, delimiter=self.delimiter, extrasaction="ignore"
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({name: row.get(name, "") for name in columns})

        ctx.put(RUN_CONTEXT_FINAL_OUTPUT_PATH, str(output_path))
        outputs.write(
            FileArtifact(
                path=str(output_path),
                metadata={
                    "row_count": len(rows),
                    "column_count": len(columns),
                    "merge_mode": self.mode,
                    "source_ports": [port for port, _, _ in sources],
                },
            ),
            OUTPUT_PORT,
        )

    # ---- 读取 ----------------------------------------------------------

    def _read_sources(
        self, inputs: JobInputStream
    ) -> list[tuple[str, list[str], list[dict[str, str]]]]:
        """按端口名自然序读入各路表。

        端口顺序必须显式排 —— JobInputStream.ports() 的顺序跟着连线顺序走，
        而连线顺序对汇聚结果是有意义的（join 以第一路为基准，concat 决定行序），
        跟着连线走等于让结果依赖 DAG 里边的书写次序。
        """
        ports = sorted(inputs.ports(), key=_natural_key)
        if len(ports) < 2:
            raise ValueError(
                f"table merge stop needs at least 2 inputs, got ports={ports}；"
                "只有一路上游说明这个节点不该是汇聚节点"
            )

        sources = []
        for port in ports:
            path = self._input_path(inputs, port)
            columns, rows = self._read_table(path, port)
            sources.append((port, columns, rows))
        return sources

    def _input_path(self, inputs: JobInputStream, port: str) -> Path:
        artifact = inputs.read(port)
        raw = getattr(artifact, "path", "") or str(getattr(artifact, "value", ""))
        if not raw:
            raise ValueError(f"table merge input artifact has no file path for port {port}")

        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"table merge input file not found: {path}")
        if not path.is_file():
            raise ValueError(f"table merge input path is not a file: {path}")
        return path

    def _read_table(self, path: Path, port: str) -> tuple[list[str], list[dict[str, str]]]:
        # utf-8 一律按 utf-8-sig 读：能吃掉 Excel 导出的 BOM，没有 BOM 时行为不变。
        # 不这么做的话首列列名会变成 "﻿时间"，join_keys 永远对不上。
        encoding = "utf-8-sig" if self.encoding.lower() in ("utf-8", "utf8") else self.encoding
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.delimiter)
            columns = [str(name) for name in (reader.fieldnames or [])]
            if not columns:
                raise ValueError(f"table merge input has no header row: {path}（端口 {port}）")
            rows = [
                {name: _cell(row.get(name)) for name in columns}
                for row in reader
            ]
        return columns, rows

    # ---- 纵向拼接 ------------------------------------------------------

    def _concat(
        self, sources: list[tuple[str, list[str], list[dict[str, str]]]]
    ) -> tuple[list[str], list[dict[str, str]]]:
        """行堆叠。各路列名取并集，缺的列留空 —— 列不完全一致就报错太脆了，
        源自不同中心的表多一列少一列很常见，留空并保留全部数据更有用。"""
        columns: list[str] = []
        for _, source_columns, _ in sources:
            for name in source_columns:
                if name not in columns:
                    columns.append(name)
        if self.source_column:
            if self.source_column in columns:
                raise ValueError(
                    f"source_column {self.source_column!r} 与数据里已有的列重名，请换一个名字"
                )
            columns.append(self.source_column)

        rows: list[dict[str, str]] = []
        for port, _, source_rows in sources:
            for row in source_rows:
                merged = {name: row.get(name, "") for name in columns}
                if self.source_column:
                    merged[self.source_column] = port
                rows.append(merged)
        return columns, rows

    # ---- 横向关联 ------------------------------------------------------

    def _join(
        self, sources: list[tuple[str, list[str], list[dict[str, str]]]]
    ) -> tuple[list[str], list[dict[str, str]]]:
        """以第一路为基准逐路关联。列名冲突加端口后缀，不做静默覆盖 ——
        两路都有 `value` 列时覆盖掉一路，结果是错的却不会报错。"""
        for port, source_columns, _ in sources:
            missing = [key for key in self.join_keys if key not in source_columns]
            if missing:
                raise ValueError(
                    f"端口 {port} 的表缺少关联键 {missing}；该表的列为 {source_columns}"
                )

        columns: list[str] = list(self.join_keys)
        accumulated: dict[tuple[str, ...], dict[str, str]] = {}
        order: list[tuple[str, ...]] = []

        for index, (port, source_columns, source_rows) in enumerate(sources):
            indexed = self._index_rows(port, source_rows)

            renamed: dict[str, str] = {}
            for name in source_columns:
                if name in self.join_keys:
                    continue
                column = self._claim(name, port, columns)
                columns.append(column)
                renamed[name] = column

            for key, row in indexed.items():
                target = accumulated.get(key)
                if target is None:
                    # 第一路建基准行；之后只有 outer 才为新键补行
                    if index > 0 and self.join_type != "outer":
                        continue
                    target = dict(zip(self.join_keys, key))
                    accumulated[key] = target
                    order.append(key)
                for name, column in renamed.items():
                    target[column] = row.get(name, "")

            if index > 0 and self.join_type == "inner":
                order = [key for key in order if key in indexed]
                accumulated = {key: accumulated[key] for key in order}

        return columns, [accumulated[key] for key in order]

    def _index_rows(
        self, port: str, rows: list[dict[str, str]]
    ) -> dict[tuple[str, ...], dict[str, str]]:
        indexed: dict[tuple[str, ...], dict[str, str]] = {}
        for row in rows:
            key = self._key_of(row)
            if key in indexed:
                raise ValueError(
                    f"端口 {port} 的表在关联键 {self.join_keys} 上有重复行 {list(key)}；"
                    "关联键必须唯一，否则关联结果会成倍膨胀"
                )
            indexed[key] = row
        return indexed

    def _key_of(self, row: dict[str, str]) -> tuple[str, ...]:
        return tuple(row.get(key, "") for key in self.join_keys)

    @staticmethod
    def _claim(name: str, port: str, taken: list[str]) -> str:
        """列名去重：先加端口后缀，仍冲突再挂序号。"""
        if name not in taken:
            return name
        candidate = f"{name}__{port}"
        if candidate not in taken:
            return candidate
        index = 2
        while f"{candidate}_{index}" in taken:
            index += 1
        return f"{candidate}_{index}"

    # ---- 输出 ----------------------------------------------------------

    def _prepare_output_path(self, ctx: JobContext) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = safe_name(ctx.get_stop_job().get_stop_name())
        job_id = ctx.get_stop_job().jid()
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / self.output_file_name


def _text(value: Any, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise TypeError(f"table merge property must be a string, got {type(value).__name__}")
    return value.strip() or default


def _cell(value: Any) -> str:
    """列数比表头多时 DictReader 会塞进一个 list，统一压成字符串。"""
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def _natural_key(text: str) -> tuple[Any, ...]:
    """input_2 排在 input_10 前面，而不是字典序的反过来。"""
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", text)
    )
