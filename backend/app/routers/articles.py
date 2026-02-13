"""
文章采集与入库 API：单条/批量写入，与来源关联；关键词提取与按标签筛选。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article, Source, Tag
from app.schemas.article import ArticleBatchCreate, ArticleCreate, ArticleResponse
from app.schemas.tag import TagResponse
from app.services.keyword_extract import extract_keywords

router = APIRouter(prefix="/articles", tags=["articles"])


def _ensure_source_exists(source_id: int | None, db: Session) -> None:
    """若提供 source_id 则校验来源存在。"""
    if source_id is None:
        return
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source id={source_id} not found")


def _get_or_create_tag(db: Session, name: str) -> Tag:
    """按名称获取或创建标签。"""
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


@router.get("", response_model=list[ArticleResponse])
def list_articles(
    tag_id: int | None = Query(None, description="按关键词/标签 ID 筛选"),
    db: Session = Depends(get_db),
):
    """文章列表；支持按标签 ID 筛选（按关键词聚合查询）。"""
    q = db.query(Article).order_by(Article.id)
    if tag_id is not None:
        q = q.join(Article.tags).filter(Tag.id == tag_id)
    return q.all()


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


@router.post("/{article_id}/extract-keywords", response_model=list[TagResponse])
def extract_article_keywords(article_id: int, db: Session = Depends(get_db)):
    """对指定文章进行关键词提取，关联到文章并返回标签列表。"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"Article id={article_id} not found")
    text = (article.title or "") + "\n" + (article.summary or "")
    keywords = extract_keywords(text)
    tags: list[Tag] = []
    for name in keywords:
        tag = _get_or_create_tag(db, name)
        tags.append(tag)
    article.tags = tags
    db.commit()
    for t in tags:
        db.refresh(t)
    return tags
