"""
文章采集与入库 API：单条/批量写入，与来源关联。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article, Source
from app.schemas.article import ArticleBatchCreate, ArticleCreate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


def _ensure_source_exists(source_id: int | None, db: Session) -> None:
    """若提供 source_id 则校验来源存在。"""
    if source_id is None:
        return
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source id={source_id} not found")


@router.get("", response_model=list[ArticleResponse])
def list_articles(db: Session = Depends(get_db)):
    """文章列表（用于验收与后续 F006 扩展筛选）。"""
    return db.query(Article).order_by(Article.id).all()


@router.post("", response_model=ArticleResponse, status_code=201)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    """单条文章入库。"""
    _ensure_source_exists(payload.source_id, db)
    article = Article(
        title=payload.title,
        url=payload.url,
        source_id=payload.source_id,
        published_at=payload.published_at,
        summary=payload.summary,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.post("/batch", response_model=list[ArticleResponse], status_code=201)
def create_articles_batch(payload: ArticleBatchCreate, db: Session = Depends(get_db)):
    """批量文章入库。"""
    for item in payload.articles:
        _ensure_source_exists(item.source_id, db)
    created = []
    for item in payload.articles:
        article = Article(
            title=item.title,
            url=item.url,
            source_id=item.source_id,
            published_at=item.published_at,
            summary=item.summary,
        )
        db.add(article)
        db.flush()  # 获得 id
        created.append(article)
    db.commit()
    for a in created:
        db.refresh(a)
    return created
