from __future__ import annotations

from typing import Any

from tests.support.test_artifacts import TraceArtifact
from cn.piflow.core.runtime_context import JobContext, ProcessContext
from cn.piflow.core.stop import ConfigurableStop
from cn.piflow.core.stream import JobInputStream, JobOutputStream


def _artifact_text(artifact: object) -> str:
    if hasattr(artifact, "describe"):
        return str(getattr(artifact, "describe")())
    if hasattr(artifact, "text"):
        return str(getattr(artifact, "text"))
    if hasattr(artifact, "value"):
        return str(getattr(artifact, "value"))
    return str(artifact)


class MockSourceStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock source stop for FlowBean tests."
    inport_list = [""]
    outport_list = [""]

    def __init__(self) -> None:
        super().__init__()
        self.path = ""
        self.format = ""
        self.last_output = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.path = str(properties.get("path", ""))
        self.format = str(properties.get("format", ""))

    def initialize(self, ctx: ProcessContext) -> None:
        print(f"[init] Source path={self.path} format={self.format}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        print(
            f"[perform] stop={ctx.get_stop_job().get_stop_name()} "
            f"params={{'path': '{self.path}', 'format': '{self.format}'}} "
            f"trace_inputs={inputs.ports()}"
        )
        artifact = TraceArtifact(
            f"source::{self.path}::{self.format}",
            stop=ctx.get_stop_job().get_stop_name(),
            params={"path": self.path, "format": self.format},
        )
        self.last_output = artifact.text
        outputs.write(artifact)
        print(f"[output] stop={ctx.get_stop_job().get_stop_name()} artifact={artifact.describe()}")


class MockSinkStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock sink stop for FlowBean tests."
    inport_list = [""]
    outport_list = [""]

    def __init__(self) -> None:
        super().__init__()
        self.output_path = ""
        self.last_input = None
        self.last_output = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.output_path = str(properties.get("output_path", ""))

    def initialize(self, ctx: ProcessContext) -> None:
        print(f"[init] Sink output_path={self.output_path}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        print(
            f"[perform] stop={ctx.get_stop_job().get_stop_name()} "
            f"params={{'output_path': '{self.output_path}'}} "
            f"trace_inputs={inputs.ports()}"
        )
        if inputs.contains():
            artifact = inputs.read()
            self.last_input = _artifact_text(artifact)
            print(
                f"[input] stop={ctx.get_stop_job().get_stop_name()} "
                f"artifact={self.last_input}"
            )
        else:
            print(f"[input] stop={ctx.get_stop_job().get_stop_name()} artifact=<empty>")
        outputs.write_properties({"output_path": self.output_path})


class MockTransformStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock transform stop for FlowBean tests."
    inport_list = [""]
    outport_list = [""]

    def __init__(self) -> None:
        super().__init__()
        self.tag = ""
        self.last_input = None
        self.last_output = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.tag = str(properties.get("tag", "transform"))

    def initialize(self, ctx: ProcessContext) -> None:
        print(f"[init] Transform tag={self.tag}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        port_names = inputs.ports()
        print(
            f"[perform] stop={ctx.get_stop_job().get_stop_name()} "
            f"params={{'tag': '{self.tag}'}} trace_inputs={port_names}"
        )
        if inputs.contains():
            artifact = inputs.read()
            self.last_input = _artifact_text(artifact)
            print(
                f"[input] stop={ctx.get_stop_job().get_stop_name()} "
                f"artifact={self.last_input}"
            )
        else:
            self.last_input = "<empty>"
        result = TraceArtifact(
            f"{self.tag}::{self.last_input}",
            stop=ctx.get_stop_job().get_stop_name(),
            params={"tag": self.tag},
        )
        self.last_output = result.text
        outputs.write(result)
        print(f"[output] stop={ctx.get_stop_job().get_stop_name()} artifact={result.describe()}")


class MockMergeStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock merge stop for FlowBean tests."
    inport_list = ["data1", "data2"]
    outport_list = [""]

    def __init__(self) -> None:
        super().__init__()
        self.last_input = {}
        self.last_output = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        return None

    def initialize(self, ctx: ProcessContext) -> None:
        print("[init] Merge")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        print(
            f"[perform] stop={ctx.get_stop_job().get_stop_name()} "
            f"params={{'inports': 'data1,data2'}} trace_inputs={inputs.ports()}"
        )
        left = inputs.read("data1")
        right = inputs.read("data2")
        left_text = _artifact_text(left)
        right_text = _artifact_text(right)
        print(
            f"[input] stop={ctx.get_stop_job().get_stop_name()} "
            f"data1={left_text} data2={right_text}"
        )
        self.last_input = {"data1": left_text, "data2": right_text}
        result = TraceArtifact(
            f"merge::{left_text}+{right_text}",
            stop=ctx.get_stop_job().get_stop_name(),
            params={"inports": "data1,data2"},
        )
        self.last_output = result.text
        outputs.write(result)
        print(f"[output] stop={ctx.get_stop_job().get_stop_name()} artifact={result.describe()}")


class MockForkStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock fork stop for FlowBean tests."
    inport_list = [""]
    outport_list = ["out1", "out2", "out3"]

    def __init__(self) -> None:
        super().__init__()
        self.outports = ["out1", "out2", "out3"]
        self.last_input = None
        self.last_output = []

    def set_properties(self, properties: dict[str, Any]) -> None:
        outports = str(properties.get("outports", "out1,out2,out3"))
        self.outports = [port.strip() for port in outports.split(",") if port.strip()]

    def initialize(self, ctx: ProcessContext) -> None:
        print(f"[init] Fork outports={self.outports}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        if inputs.contains():
            artifact = inputs.read()
            self.last_input = _artifact_text(artifact)
        else:
            self.last_input = "<empty>"
        print(
            f"[perform] stop={ctx.get_stop_job().get_stop_name()} "
            f"params={{'outports': '{','.join(self.outports)}'}} trace_inputs={inputs.ports()} "
            f"input={self.last_input}"
        )
        for port in self.outports:
            result = TraceArtifact(
                f"fork::{port}::{self.last_input}",
                stop=ctx.get_stop_job().get_stop_name(),
                params={"outports": ",".join(self.outports)},
            )
            outputs.write(result, port)
            self.last_output.append(result.text)
            print(
                f"[output] stop={ctx.get_stop_job().get_stop_name()} "
                f"port={port} artifact={result.describe()}"
            )


class MockFilePathSinkStop(ConfigurableStop):
    author_email = "test@piflow.cn"
    description = "Mock sink that records an input file path."
    inport_list = [""]
    outport_list = [""]

    def __init__(self) -> None:
        super().__init__()
        self.in_port = ""
        self.last_input_path = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.in_port = str(properties.get("in_port", ""))

    def initialize(self, ctx: ProcessContext) -> None:
        return None

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        artifact = inputs.read(self.in_port)
        self.last_input_path = str(getattr(artifact, "path", "") or artifact.value)
        outputs.write_properties({"input_path": self.last_input_path})
