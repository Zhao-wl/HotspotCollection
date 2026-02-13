"""
文章关键词提取与关联：供文章 API 与采集服务复用。
对指定文章使用 LangExtract 提取关键词，并关联到文章的 tags。
"""
from sqlalchemy.orm import Session

from app.models import Article, Tag
from app.services.keyword_extract import extract_keywords


def get_or_create_tag(db: Session, name: str) -> Tag:
    """按名称获取或创建标签。"""
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def extract_and_attach_keywords(db: Session, article: Article) -> list[str]:
    """
    对文章使用 LangExtract 提取关键词，关联到 article.tags，并返回关键词名称列表。
    若未配置 API Key 或提取失败，返回空列表，不修改 article.tags。
    """
    text = (article.title or "") + "\n" + (article.summary or "")
    keywords = extract_keywords(text)
    tags: list[Tag] = []
    for name in keywords:
        tag = get_or_create_tag(db, name)
        tags.append(tag)
    article.tags = tags
    return [t.name for t in tags]
