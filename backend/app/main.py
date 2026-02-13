"""
HotspotCollection 后端入口
FastAPI + SQLite，提供健康检查与后续文章/来源 API。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HotspotCollection API",
    description="热点文章收集服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """健康检查，用于 init 脚本与运维探测。"""
    return {"status": "ok", "service": "HotspotCollection"}
