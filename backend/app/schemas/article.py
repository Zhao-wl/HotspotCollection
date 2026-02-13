"""
文章录入/响应的请求与响应 schema。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# 避免循环导入：在 ArticleListResponse 中使用前向引用或延迟导入


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


class ArticleListResponse(BaseModel):
    """文章列表项（展示用）：含标题、标签、来源、原文链接、日期。"""
    id: int
    title: str
    url: str
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    tags: list["TagInArticle"] = Field(default_factory=list, description="关联标签")

    class Config:
        from_attributes = True


class TagInArticle(BaseModel):
    """列表项内嵌的标签简要信息。"""
    id: int
    name: str

    class Config:
        from_attributes = True


class ArticleBatchCreate(BaseModel):
    """批量文章入库请求体。"""
    articles: list[ArticleCreate] = Field(..., min_length=1, description="待入库文章列表")


# 解析前向引用
ArticleListResponse.model_rebuild()
