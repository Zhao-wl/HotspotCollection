"""
文章录入/响应的请求与响应 schema。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    """文章创建共用字段。"""
    title: str = Field(..., min_length=1, max_length=512, description="标题")
    url: str = Field(..., min_length=1, description="原文链接")
    source_id: Optional[int] = Field(None, description="来源 ID，与来源配置关联")
    published_at: Optional[datetime] = Field(None, description="发布日期")
    summary: Optional[str] = Field(None, description="摘要")


class ArticleCreate(ArticleBase):
    """单条文章创建请求体。"""
    pass


class ArticleResponse(ArticleBase):
    """文章响应体。"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleBatchCreate(BaseModel):
    """批量文章入库请求体。"""
    articles: list[ArticleCreate] = Field(..., min_length=1, description="待入库文章列表")
