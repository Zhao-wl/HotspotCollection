"""
标签/关键词 API：列表与按关键词聚合查询（文章列表见 articles 的 tag_id 筛选）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag
from app.schemas.tag import TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db)):
    """标签列表，用于按关键词聚合展示。"""
    return db.query(Tag).order_by(Tag.id).all()
