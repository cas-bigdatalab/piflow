import threading

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from infra.config_loader import get_settings

_scheduler = None
_lock = threading.Lock()

def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    with _lock:
        if _scheduler is not None:
            return _scheduler

        settings = get_settings()
        db = settings.database
        host=db.host
        port=db.port
        user=db.user
        password=db.password
        dbname=db.name

        jobstores = {
            "default": SQLAlchemyJobStore(url=f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")
        }
        executors = {
            "default": ThreadPoolExecutor(20),
            "processpool": ProcessPoolExecutor(5)
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        _scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

        return _scheduler

