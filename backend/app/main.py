"""
HotspotCollection 后端入口
FastAPI + SQLite，提供健康检查与后续文章/来源 API；后台长线任务定时执行文章采集。
"""
import logging
import os
import threading
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db, SessionLocal
from app.routers import articles, sources, tags, collect
from app.routers.collect import set_last_result
from app.services.collector import run_collection

logger = logging.getLogger(__name__)

# 后台采集间隔（秒），默认 30 分钟
COLLECT_INTERVAL_SEC = int(os.getenv("COLLECT_INTERVAL_SEC", "1800"))
# 启动后首次采集延迟（秒），避免与启动争抢
COLLECT_FIRST_DELAY_SEC = int(os.getenv("COLLECT_FIRST_DELAY_SEC", "60"))


def _collect_worker(stop_event: threading.Event) -> None:
    """后台线程：定时执行采集，直到 stop_event 被设置。"""
    time.sleep(COLLECT_FIRST_DELAY_SEC)
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                result = run_collection(db)
                set_last_result(result)
                logger.info(
                    "collect done: sources_ok=%s sources_fail=%s articles_added=%s",
                    result.get("sources_ok"),
                    result.get("sources_fail"),
                    result.get("articles_added"),
                )
            finally:
                db.close()
        except Exception as e:
            logger.exception("collect worker error: %s", e)
        if stop_event.wait(timeout=COLLECT_INTERVAL_SEC):
            break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表，启动后台采集线程；关闭时停止线程。"""
    init_db()
    stop_event = threading.Event()
    collect_thread = threading.Thread(target=_collect_worker, args=(stop_event,), daemon=True)
    collect_thread.start()
    yield
    stop_event.set()
    collect_thread.join(timeout=5.0)


app = FastAPI(
    title="HotspotCollection API",
    description="热点文章收集服务",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(sources.router)
app.include_router(articles.router)
app.include_router(tags.router)
app.include_router(collect.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """捕获未处理异常，返回 500 并带上详情便于排查。HTTPException 交给 FastAPI 默认处理。"""
    if isinstance(exc, HTTPException):
        raise exc
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__, "_traceback": tb},
    )


@app.get("/health")
def health():
    """健康检查，用于 init 脚本与运维探测。"""
    return {"status": "ok", "service": "HotspotCollection"}
