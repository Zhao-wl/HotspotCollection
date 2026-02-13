"""
文章采集与入库 API：单条/批量写入，与来源关联；关键词提取与按标签筛选。
文章展示 API：按日期、标签、来源筛选，分页，返回标题/标签/来源/链接/日期。
"""
from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Article, Source, Tag, article_tag
from app.schemas.article import (
    ArticleBatchCreate,
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    TagInArticle,
)
from app.schemas.tag import TagResponse
from app.services.article_keywords import extract_and_attach_keywords

router = APIRouter(prefix="/articles", tags=["articles"])


def _ensure_source_exists(source_id: int | None, db: Session) -> None:
    """若提供 source_id 则校验来源存在。"""
    if source_id is None:
        return
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source id={source_id} not found")


def _article_to_list_response(article: Article) -> ArticleListResponse:
    """将 ORM Article（已 loaded source/tags）转为 ArticleListResponse。"""
    return ArticleListResponse(
        id=article.id,
        title=article.title,
        url=article.url,
        published_at=article.published_at,
        created_at=article.created_at,
        source_id=article.source_id,
        source_name=article.source.name if article.source else None,
        tags=[TagInArticle(id=t.id, name=t.name) for t in article.tags],
    )


@router.get("", response_model=list[ArticleListResponse])
def list_articles(
    tag_id: Annotated[int | None, Query(description="按关键词/标签 ID 筛选")] = None,
    source_id: Annotated[int | None, Query(description="按来源 ID 筛选")] = None,
    date_from: Annotated[
        date | None, Query(description="发布日期起（含）")
    ] = None,
    date_to: Annotated[date | None, Query(description="发布日期止（含）")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    offset: Annotated[int, Query(ge=0, description="偏移量")] = 0,
    db: Session = Depends(get_db),
):
    """文章列表（展示用）：按日期、标签、来源筛选，分页；返回标题、标签、来源、原文链接、日期。"""
    q = (
        db.query(Article)
        .options(
            joinedload(Article.source),
            joinedload(Article.tags),
        )
        .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
    )
    if tag_id is not None:
        # 用子查询避免 join 导致重复行，不依赖 .unique()
        sub = db.query(Article.id).join(Article.tags).filter(Tag.id == tag_id)
        q = q.filter(Article.id.in_(sub))
    if source_id is not None:
        q = q.filter(Article.source_id == source_id)
    if date_from is not None:
        q = q.filter(Article.published_at >= datetime.combine(date_from, time.min))
    if date_to is not None:
        q = q.filter(Article.published_at <= datetime.combine(date_to, time(23, 59, 59, 999999)))
    rows = q.offset(offset).limit(limit).all()
    return [_article_to_list_response(a) for a in rows]


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


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: int, db: Session = Depends(get_db)):
    """删除指定文章（同时移除其与标签的关联）。"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"Article id={article_id} not found")
    db.delete(article)
    db.commit()
    return None


@router.post("/clean-duplicates")
def clean_duplicate_articles(db: Session = Depends(get_db)):
    """
    清理重复文章：按原文链接 url 分组，每组只保留一条（保留 id 最小的），其余删除。
    返回删除的数量及受影响的 url 数量。
    """
    from sqlalchemy import func

    # 找出有重复的 url：按 url 分组，count > 1
    dup_urls = (
        db.query(Article.url)
        .group_by(Article.url)
        .having(func.count(Article.id) > 1)
        .all()
    )
    dup_urls = [r[0] for r in dup_urls]
    deleted_count = 0
    for url in dup_urls:
        articles = (
            db.query(Article).filter(Article.url == url).order_by(Article.id.asc()).all()
        )
        # 保留第一条（id 最小），删除其余
        for a in articles[1:]:
            db.delete(a)
            deleted_count += 1
    db.commit()
    return {
        "deleted_count": deleted_count,
        "urls_with_duplicates": len(dup_urls),
    }


@router.post("/delete-all")
def delete_all_articles(db: Session = Depends(get_db)):
    """删除数据库中全部文章（同时清除文章-标签关联）。返回删除条数。"""
    count = db.query(Article).count()
    db.query(Article).delete()
    db.commit()
    return {"deleted_count": count}


@router.post("/fix-missing-keywords")
def fix_missing_keywords(db: Session = Depends(get_db)):
    """
    批量修复：找出所有已入库但无关键词（无 tags）的文章，逐个进行关键词提取并关联。
    返回修复数量及错误信息。仅当某篇文章实际补充了至少一个关键词时才计入 fixed_count。
    """
    has_tag_sub = db.query(article_tag.c.article_id).distinct()
    without_keywords = (
        db.query(Article).filter(~Article.id.in_(has_tag_sub)).all()
    )
    fixed_count = 0
    errors: list[str] = []
    for article in without_keywords:
        try:
            kw_list = extract_and_attach_keywords(db, article)
            if kw_list:
                fixed_count += 1
        except Exception as e:
            title_preview = (article.title or "")[:30] + ("…" if len(article.title or "") > 30 else "")
            errors.append(f"文章 id={article.id} ({title_preview}): {e}")
    db.commit()
    return {
        "total_without_keywords": len(without_keywords),
        "fixed_count": fixed_count,
        "errors": errors,
    }


@router.post("/{article_id}/extract-keywords", response_model=list[TagResponse])
def extract_article_keywords(article_id: int, db: Session = Depends(get_db)):
    """对指定文章进行关键词提取，关联到文章并返回标签列表。"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail=f"Article id={article_id} not found")
    extract_and_attach_keywords(db, article)
    db.commit()
    for t in article.tags:
        db.refresh(t)
    return article.tags
