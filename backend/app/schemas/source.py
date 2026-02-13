"""
来源配置的请求/响应 schema。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    """来源创建/更新共用字段。"""
    name: str = Field(..., min_length=1, max_length=255, description="来源名称")
    type_or_kind: Optional[str] = Field(None, max_length=64, description="类型，如 rss, api, manual")
    url_or_config: Optional[str] = Field(None, description="URL 或 JSON 配置")


class SourceCreate(SourceBase):
    """创建来源请求体。"""
    pass


class SourceUpdate(BaseModel):
    """更新来源请求体（部分字段可选）。"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type_or_kind: Optional[str] = Field(None, max_length=64)
    url_or_config: Optional[str] = None


class SourceResponse(SourceBase):
    """来源响应体。"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
