"""
HotspotCollection 数据模型：来源、文章、标签及文章-标签关联。
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship

from app.database import Base


# 文章-标签多对多关联表
article_tag = Table(
    "article_tag",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Source(Base):
    """热点文章来源配置。"""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type_or_kind = Column(String(64), nullable=True)  # 如 rss, api, manual
    url_or_config = Column(Text, nullable=True)  # URL 或 JSON 配置
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    articles = relationship("Article", back_populates="source")


class Article(Base):
    """文章：标题、原文链接、来源、日期等。"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    url = Column(Text, nullable=False)  # 原文链接
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    published_at = Column(DateTime, nullable=True)  # 发布日期
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)

    source = relationship("Source", back_populates="articles")
    tags = relationship("Tag", secondary=article_tag, back_populates="articles")


class Tag(Base):
    """标签/关键词。"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    articles = relationship("Article", secondary=article_tag, back_populates="tags")
