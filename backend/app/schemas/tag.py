"""
标签/关键词的请求与响应 schema。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TagResponse(BaseModel):
    """标签响应体。"""
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagWithCountResponse(TagResponse):
    """标签及关联文章数（用于聚合查询）。"""
    article_count: int = 0
