import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from infra.logging import init_logging
from runtime.chat_store import get_user_threads, delete_thread
from runtime.engine import AgentEngine
from runtime.workspace_manager import WorkspaceManager


log = logging.getLogger("flow.api")

app = FastAPI()
engine = AgentEngine()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "default_user"

class ThreadListRequest(BaseModel):
    user_id: str

class DeleteThreadRequest(BaseModel):
    user_id: str
    thread_id: str

@app.on_event("startup")
async def startup():
    init_logging()
    await engine.initialize()
    log.info("DeepAgent server started")


@app.post("/chat")
async def chat(req: ChatRequest):
    result = await engine.run(req.message, req.thread_id, req.user_id)
    return {"events": result}

@app.post("/threads/getTitles")
async def get_threads(req: ThreadListRequest):
    threads = get_user_threads(req.user_id)
    return {"threads": threads}

@app.post("/thread/delete")
async def delete_thread_api(req: DeleteThreadRequest):
    delete_thread(req.user_id, req.thread_id)
    return {"success": True}


@app.post("/workspace/upload")
async def upload_workspace_file(
    file: UploadFile = File(...),
    target_dir: str = Form("temp"),
    filename: str = Form(""),
):
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    safe_name = Path(filename or file.filename or "").name.strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename is required")

    virtual_path = f"/{target_dir.strip().strip('/')}/{safe_name}"

    try:
        destination = workspace.resolve_virtual_path(virtual_path, create_parent=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = await file.read()
    destination.write_bytes(content)

    return {
        "path": virtual_path,
        "filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }


@app.get("/workspace/download")
async def download_workspace_file(path: str):
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    try:
        source = workspace.resolve_virtual_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not source.exists() or not source.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(
        path=source,
        filename=source.name,
        media_type="application/octet-stream",
    )


if __name__ == "__main__":
    init_logging()
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
