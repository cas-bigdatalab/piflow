import logging

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from infra.logging import init_logging
from runtime.chat_store import get_user_threads, delete_thread
from runtime.engine import AgentEngine


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


if __name__ == "__main__":
    init_logging()
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
