import logging
import os
from pathlib import Path

from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from infra.config_loader import get_settings
from infra.logging import init_logging
from repositories.datasource_catalog_repository import initialize_datasource_catalog_schema
from runtime.engine import AgentEngine
from runtime.planner_engine import PlannerEngine

from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.community_router import router as community_router
from routers.corpus_router import router as corpus_router
from routers.dag_panel_api import router as dag_router
from routers.dag_runtime_api import router as dag_runtime_router
from routers.dataspace_router import router as dataspace_router
from routers.storage_router import router as storage_router
from routers.user_router import router as user_router
from routers.workspace_router import router as workspace_router
from routers.subagent.workflow_advisor.workflow_advisor_router import router as workflow_advisor_router

log = logging.getLogger("flow.api")
PROJECT_ROOT = Path(__file__).resolve().parent
STORAGE_DIR = PROJECT_ROOT / "storage"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logging()
    log.info("starting API mode")

    initialize_datasource_catalog_schema()
    engine = AgentEngine()
    planner_engine = PlannerEngine()
    await engine.initialize()
    await planner_engine.initialize()
    app.state.engine = engine
    app.state.planner_engine = planner_engine

    log.info("DeepAgent server started")
    try:
        yield
    finally:
        planner_engine = getattr(app.state, "planner_engine", None)
        if planner_engine is not None:
            await planner_engine.shutdown()

        engine = getattr(app.state, "engine", None)
        if engine is not None:
            await engine.shutdown()


app = FastAPI(lifespan=lifespan)

# 新建父路由，统一加 /api 前缀
api_router = APIRouter(prefix="/api/piflow/v1")

api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(community_router)
api_router.include_router(corpus_router)
api_router.include_router(dag_router)
api_router.include_router(dag_runtime_router)
api_router.include_router(dataspace_router)
api_router.include_router(storage_router)
api_router.include_router(user_router)
api_router.include_router(workspace_router)
api_router.include_router(workflow_advisor_router)

# 把父router挂载到app
app.include_router(api_router)

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

if __name__ == "__main__":
    init_logging()
    settings = get_settings()
    enable_reload = os.getenv("FLOW_API_RELOAD", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    port = settings.app.port

    if enable_reload:
        log.info("starting uvicorn with reload enabled on port %s", port)
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=port,
            reload=True,
        )
    else:
        log.info("starting uvicorn without reload on port %s", port)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
        )
