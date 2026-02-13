"""
来源配置 CRUD API。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    """创建来源配置。"""
    try:
        url_or_config = (payload.url_or_config or "").strip() or None
        type_or_kind = (payload.type_or_kind or "").strip() or None
        source = Source(
            name=payload.name.strip(),
            type_or_kind=type_or_kind,
            url_or_config=url_or_config,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建来源失败: {str(e)}") from e


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    """列表来源配置。"""
    return db.query(Source).order_by(Source.id).all()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """按 ID 获取单条来源。"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    """更新来源配置（部分字段）。"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(source, k, v)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """删除来源配置。"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return None
