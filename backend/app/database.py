"""
数据库连接与会话。
SQLite，应用启动时建表（见 main lifespan）。
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 默认使用项目 backend 目录下的 data.db
_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_PATH}")

# 若环境变量是 aiosqlite，建表时使用同步 URL
if "aiosqlite" in DATABASE_URL:
    _sync_url = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://", 1)
else:
    _sync_url = DATABASE_URL

engine = create_engine(_sync_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """创建所有表（迁移用）。应用启动时调用。"""
    from app import models  # noqa: F401  # 确保模型已注册到 Base.metadata

    Base.metadata.create_all(bind=engine)


def get_db():
    """依赖注入：获取数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
