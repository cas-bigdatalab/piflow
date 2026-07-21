from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from runtime.planner_engine import PLANNER_EXECUTE_SPEC_MARKER, PlannerEngine


class TemporaryWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root

    def to_user_virtual_path(self, user_id: str, path: str) -> str:
        relative = path.strip().lstrip("/")
        if not relative or ".." in Path(relative).parts:
            raise ValueError("unsafe user workspace path")
        return f"/users/{user_id}/{relative}"

    def snapshot_downloadables(self) -> dict[str, tuple[int, int]]:
        return {}

    def detect_changed_downloadables(self, before: dict[str, tuple[int, int]]) -> list[str]:
        assert before == {}
        return []


class UploadedFileReadingPlannerAgent:
    """Simulates the planner agent reading the attachment path it receives."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.received_content = ""

    async def astream(self, input_message, config=None, stream_mode=None):  # noqa: ANN001
        self.received_content = input_message["messages"][0]["content"]
        attachment_path = "/users/alice/temp/thread-1/upload.csv"
        assert attachment_path in self.received_content

        file_path = self.workspace_root / attachment_path.lstrip("/")
        file_content = file_path.read_text(encoding="utf-8")
        answer = f"已读取上传文件：{file_content.strip()}"
        yield {
            "planner": {
                "messages": [
                    SimpleNamespace(
                        type="ai",
                        content=answer,
                        tool_calls=[],
                        response_metadata={},
                    )
                ]
            }
        }


@pytest.mark.asyncio
async def test_planner_agent_can_read_uploaded_user_file_without_chat_persistence(tmp_path: Path):
    workspace_root = tmp_path / "workspace"
    uploaded_file = workspace_root / "users" / "alice" / "temp" / "thread-1" / "upload.csv"
    uploaded_file.parent.mkdir(parents=True)
    uploaded_file.write_text("name,score\nAda,100\n", encoding="utf-8")

    agent = UploadedFileReadingPlannerAgent(workspace_root)
    engine = PlannerEngine()
    engine.agent = agent
    engine.initialized = True

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(workspace_root)):
        answer = await engine.run(
            "请读取我上传的 CSV 文件内容。",
            thread_id="thread-1",
            user_id="alice",
            attachments=["/temp/thread-1/upload.csv"],
            request_id="planner-upload-test",
        )

    assert answer == "已读取上传文件：name,score\nAda,100"
    assert "/users/alice/temp/thread-1/upload.csv" in agent.received_content


class ConfirmedPlannerAgent:
    async def astream(self, input_message, config=None, stream_mode=None):  # noqa: ANN001
        message = SimpleNamespace(
            type="ai",
            content=(
                f"{PLANNER_EXECUTE_SPEC_MARKER}\n"
                '{"name":"text-summarizer","description":"总结文本。",'
                '"input_params":[{"name":"input_text","type":"string",'
                '"required":true,"description":"待总结文本"}],'
                '"output_params":[{"name":"summary","type":"string",'
                '"description":"摘要文本"}]}'
            ),
            tool_calls=[],
            response_metadata={},
        )
        if stream_mode:
            yield "messages", (message, {"langgraph_node": "planner"})
            return
        yield {"planner": {"messages": [message]}}


@pytest.mark.asyncio
async def test_planner_executes_confirmed_skill_spec(tmp_path: Path):
    engine = PlannerEngine()
    engine.agent = ConfirmedPlannerAgent()
    engine.initialized = True
    generated = {
        "skill_dir": "skills/generated/text-summarizer",
        "skill_md": "skills/generated/text-summarizer/SKILL.md",
        "dag_skill_id": "generated-text-summarizer",
    }

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(tmp_path)), patch(
        "runtime.planner_engine._generate_planner_skill", return_value=generated
    ) as generate:
        answer = await engine.run("直接进入", thread_id="thread-2", request_id="planner-execute-test")

    generate.assert_called_once()
    spec, thread_id = generate.call_args.args
    assert spec["name"] == "text-summarizer"
    assert thread_id == "thread-2"
    assert "Skill 已生成并注册。" in answer
    assert "skills/generated/text-summarizer" in answer


@pytest.mark.asyncio
async def test_planner_loads_skill_followup_as_llm_context(tmp_path: Path):
    class FollowupPlannerAgent:
        def __init__(self):
            self.calls = []

        async def astream(self, input_message, config=None, stream_mode=None):  # noqa: ANN001
            content = input_message["messages"][0]["content"]
            self.calls.append(content)
            answer = (
                "已根据冲突规则改为 xlsx-validate-private。"
                if len(self.calls) == 2
                else f'{PLANNER_EXECUTE_SPEC_MARKER}\n{{"name":"xlsx_validate","description":"validate"}}'
            )
            message = SimpleNamespace(type="ai", content=answer, tool_calls=[], response_metadata={})
            yield {"planner": {"messages": [message]}}

    engine = PlannerEngine()
    engine.agent = FollowupPlannerAgent()
    engine.initialized = True
    followup = "内部参考：`xlsx_validate` 名称不可用，请改名。"

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(tmp_path)), patch(
        "runtime.planner_engine._generate_planner_skill", return_value={"followup_prompt": followup}
    ):
        answer = await engine.run("生成 xlsx 校验 skill", thread_id="thread-followup")

    assert answer == "已根据冲突规则改为 xlsx-validate-private。"
    assert followup in engine.agent.calls[1]
    assert "以下是工具执行后的参考上下文" in engine.agent.calls[1]


@pytest.mark.asyncio
async def test_planner_reports_existing_skill_without_crashing(tmp_path: Path):
    engine = PlannerEngine()
    engine.agent = ConfirmedPlannerAgent()
    engine.initialized = True

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(tmp_path)), patch(
        "runtime.planner_engine._generate_planner_skill",
        side_effect=FileExistsError("skill already exists: skills/generated/text-summarizer"),
    ):
        answer = await engine.run("直接进入")

    assert "skill already exists" in answer
    assert "覆盖生成" in answer


@pytest.mark.asyncio
async def test_planner_stream_executes_confirmed_skill_spec(tmp_path: Path):
    engine = PlannerEngine()
    engine.agent = ConfirmedPlannerAgent()
    engine.initialized = True
    generated = {
        "skill_dir": "skills/generated/text-summarizer",
        "skill_md": "skills/generated/text-summarizer/SKILL.md",
        "dag_skill_id": "generated-text-summarizer",
    }

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(tmp_path)), patch(
        "runtime.planner_engine._generate_planner_skill", return_value=generated
    ):
        events = [event async for event in engine.stream_chat("直接进入", thread_id="thread-3")]

    assert any(event.get("stage") == "executing_skill" for event in events)
    assert events[-1]["content"].startswith("Skill 已生成并注册。")


@pytest.mark.asyncio
async def test_planner_returns_visible_error_for_empty_model_response(tmp_path: Path):
    class EmptyPlannerAgent:
        async def astream(self, input_message, config=None, stream_mode=None):  # noqa: ANN001
            yield {"planner": {"messages": []}}

    engine = PlannerEngine()
    engine.agent = EmptyPlannerAgent()
    engine.initialized = True

    with patch("runtime.planner_engine.WorkspaceManager", return_value=TemporaryWorkspace(tmp_path)):
        answer = await engine.run("直接进入")

    assert answer == "未收到可执行的 skill 规格，请重新确认生成请求。"
