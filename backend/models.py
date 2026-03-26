"""
StyleMate 数据模型
使用 SQLModel（SQLAlchemy + Pydantic 融合）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


# ============ 数据库模型 ============

class User(SQLModel, table=True):
    """用户表 —— 极简，只存 openid"""
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    openid: str = Field(unique=True, index=True, max_length=128)
    created_at: datetime = Field(default_factory=datetime.now)


class ClothingItem(SQLModel, table=True):
    """衣物表 —— AI 识别后的结构化数据"""
    __tablename__ = "clothing_items"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    image_url: str = Field(default="")                   # 原图相对路径
    thumbnail_url: str | None = Field(default=None)      # 抠图后相对路径
    category: str = Field(default="", max_length=32)     # 上衣/裤装/裙装/外套/鞋/包/配饰
    sub_category: str | None = Field(default=None, max_length=32)  # T恤/衬衫/牛仔裤...
    color: str = Field(default="", max_length=32)        # 主色调
    style: str = Field(default="", max_length=64)        # 风格标签
    season: str | None = Field(default=None, max_length=32)        # 适合季节
    ai_description: str | None = Field(default=None)     # AI 一句话描述
    is_hidden: bool = Field(default=False)               # 临时屏蔽
    created_at: datetime = Field(default_factory=datetime.now)


class Outfit(SQLModel, table=True):
    """搭配方案表"""
    __tablename__ = "outfits"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    item_ids: str = Field(default="")                    # 逗号分隔的衣物 ID
    description: str = Field(default="")                 # AI 搭配说明
    style_tags: str | None = Field(default=None)         # 逗号分隔的风格标签
    reason: str | None = Field(default=None)             # 搭配理由
    card_url: str | None = Field(default=None)           # 搭配卡片图路径
    is_favorite: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)


# ============ API 请求/响应模型 ============

class ClothingItemResponse(SQLModel):
    """衣物响应模型"""
    id: int
    image_url: str
    thumbnail_url: Optional[str] = None
    category: str
    sub_category: Optional[str] = None
    color: str
    style: str
    season: Optional[str] = None
    ai_description: Optional[str] = None
    created_at: datetime


class WardrobeResponse(SQLModel):
    """衣橱列表响应"""
    items: list[ClothingItemResponse]
    total: int


class OutfitItemDetail(SQLModel):
    """搭配中的单个衣物"""
    id: int
    thumbnail_url: Optional[str] = None
    category: str
    color: str


class OutfitResponse(SQLModel):
    """单个搭配方案响应"""
    id: int
    items: list[OutfitItemDetail]
    description: str
    style_tags: list[str]
    reason: Optional[str] = None
    card_url: Optional[str] = None
    created_at: datetime


class RecommendResponse(SQLModel):
    """搭配推荐响应"""
    outfits: list[OutfitResponse]


class RecommendRequest(SQLModel):
    """搭配推荐请求"""
    openid: str
    item_ids: Optional[list[int]] = None  # 不传则使用全部衣物
