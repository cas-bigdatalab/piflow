from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from runtime.planner_engine import PlannerEngine


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
