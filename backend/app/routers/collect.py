"""
采集任务 API：手动触发一次采集、查询最近一次结果与后台任务状态；支持按来源 ID 单独采集。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.collector import run_collection, run_collection_for_source

router = APIRouter(prefix="/collect", tags=["collect"])

# 最近一次采集结果（含手动触发与后台任务执行），供 GET /collect/status 使用
_last_run_result: dict | None = None


def _set_last_result(result: dict) -> None:
    global _last_run_result
    _last_run_result = result


def get_last_result() -> dict | None:
    return _last_run_result


def set_last_result(result: dict) -> None:
    """供后台采集线程调用，更新最近一次结果。"""
    _set_last_result(result)


@router.post("/run")
def trigger_collect(db: Session = Depends(get_db)):
    """手动触发一次采集，对全部 rss/api 来源拉取并入库。"""
    result = run_collection(db)
    _set_last_result(result)
    return result


@router.post("/run/{source_id}")
def trigger_collect_source(source_id: int, db: Session = Depends(get_db)):
    """对指定来源执行一次采集；仅 rss/api 且已配置 URL 的来源可采集。"""
    result = run_collection_for_source(db, source_id)
    if not result.get("ok") and result.get("error") == "来源不存在":
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/status")
def collect_status():
    """返回最近一次采集结果；若无则返回空。后台任务状态见 PROJECT_README。"""
    last = get_last_result()
    if last is None:
        return {"last_run": None, "message": "尚未执行过采集"}
    return {"last_run": last}
