"""
StyleMate 搭搭 — FastAPI 主应用
极速 MVP：3 个核心接口
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, create_engine, select

import config
from ai_service import recognize_clothing, recommend_outfits
from image_service import generate_outfit_card, remove_background, save_upload_image
from models import (
    ClothingItem,
    ClothingItemResponse,
    Outfit,
    OutfitItemDetail,
    OutfitResponse,
    RecommendRequest,
    RecommendResponse,
    User,
    WardrobeResponse,
)

# ============ 日志配置 ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ============ 数据库引擎 ============
engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite 需要
)


# ============ 应用生命周期 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时创建表"""
    logger.info("🚀 StyleMate 启动中...")
    SQLModel.metadata.create_all(engine)
    logger.info("✅ 数据库表已就绪")
    yield
    logger.info("👋 StyleMate 关闭")


# ============ 创建 FastAPI 应用 ============
app = FastAPI(
    title="StyleMate 搭搭",
    description="AI 穿搭助手 — 拍照建衣橱，智能出搭配",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS（小程序请求需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（图片访问）
app.mount("/static/uploads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="uploads")
app.mount("/static/processed", StaticFiles(directory=str(config.PROCESSED_DIR)), name="processed")
app.mount("/static/cards", StaticFiles(directory=str(config.CARDS_DIR)), name="cards")


# ============ 辅助函数 ============

def get_or_create_user(openid: str) -> User:
    """获取或创建用户（静默登录）"""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.openid == openid)).first()
        if not user:
            user = User(openid=openid)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"新用户创建: openid={openid}, id={user.id}")
        return user


# ============ 接口 1：上传衣物 ============

@app.post("/api/upload", response_model=ClothingItemResponse, summary="上传衣物")
async def upload_clothing(
    image: UploadFile = File(..., description="衣物照片"),
    openid: str = Form(..., description="用户 openid"),
):
    """
    上传衣物照片 → AI 自动识别 → 抠图去背景 → 存入衣橱

    处理流程：
    1. 保存原图
    2. AI 多模态模型识别衣物属性
    3. rembg 抠图去背景
    4. 存入数据库
    5. 返回识别结果
    """
    # 校验文件大小
    contents = await image.read()
    if len(contents) > config.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 4MB")

    # 校验文件类型
    if image.filename:
        from pathlib import Path as P
        ext = P(image.filename).suffix.lower()
        if ext and ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}")

    # 获取/创建用户
    user = get_or_create_user(openid)

    # Step 1: 保存原图
    image_url = save_upload_image(contents, image.filename or "photo.jpg")
    logger.info(f"原图已保存: {image_url}")

    # Step 2: AI 识别衣物
    full_image_path = str(config.BASE_DIR / image_url)
    recognition = await recognize_clothing(full_image_path)
    logger.info(f"AI 识别结果: {recognition}")

    # Step 3: 抠图去背景
    thumbnail_url = remove_background(image_url)
    logger.info(f"抠图完成: {thumbnail_url}")

    # Step 4: 存入数据库
    clothing = ClothingItem(
        user_id=user.id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        category=recognition.get("category", "上衣"),
        sub_category=recognition.get("sub_category"),
        color=recognition.get("color", "未识别"),
        style=recognition.get("style", "未识别"),
        season=recognition.get("season"),
        ai_description=recognition.get("description"),
    )

    with Session(engine) as session:
        session.add(clothing)
        session.commit()
        session.refresh(clothing)
        logger.info(f"衣物入库: id={clothing.id}, category={clothing.category}")

        return ClothingItemResponse(
            id=clothing.id,
            image_url=f"/static/{clothing.image_url}",
            thumbnail_url=f"/static/{clothing.thumbnail_url}" if clothing.thumbnail_url else None,
            category=clothing.category,
            sub_category=clothing.sub_category,
            color=clothing.color,
            style=clothing.style,
            season=clothing.season,
            ai_description=clothing.ai_description,
            created_at=clothing.created_at,
        )


# ============ 接口 2：获取衣橱 ============

@app.get("/api/wardrobe", response_model=WardrobeResponse, summary="获取衣橱")
async def get_wardrobe(openid: str):
    """
    获取用户的所有衣物列表
    """
    user = get_or_create_user(openid)

    with Session(engine) as session:
        items = session.exec(
            select(ClothingItem)
            .where(ClothingItem.user_id == user.id)
            .where(ClothingItem.is_hidden == False)
            .order_by(ClothingItem.created_at.desc())
        ).all()

        item_responses = [
            ClothingItemResponse(
                id=item.id,
                image_url=f"/static/{item.image_url}",
                thumbnail_url=f"/static/{item.thumbnail_url}" if item.thumbnail_url else None,
                category=item.category,
                sub_category=item.sub_category,
                color=item.color,
                style=item.style,
                season=item.season,
                ai_description=item.ai_description,
                created_at=item.created_at,
            )
            for item in items
        ]

        return WardrobeResponse(items=item_responses, total=len(item_responses))


# ============ 接口 3：AI 搭配推荐 ============

@app.post("/api/recommend", response_model=RecommendResponse, summary="AI 搭配推荐")
async def recommend(req: RecommendRequest):
    """
    AI 智能搭配推荐

    从用户衣橱中选取衣物，生成 3 套搭配方案，并生成搭配卡片。

    - 可以指定 item_ids 来限定使用哪些衣物
    - 不传 item_ids 则使用衣橱中全部衣物
    """
    user = get_or_create_user(req.openid)

    with Session(engine) as session:
        # 查询衣物
        query = (
            select(ClothingItem)
            .where(ClothingItem.user_id == user.id)
            .where(ClothingItem.is_hidden == False)
        )

        if req.item_ids:
            query = query.where(ClothingItem.id.in_(req.item_ids))

        items = session.exec(query).all()

        if len(items) < 2:
            raise HTTPException(
                status_code=400,
                detail="衣橱中至少需要 2 件衣物才能搭配哦～快去添加衣物吧！",
            )

        # 构建衣物数据给 AI
        wardrobe_data = [
            {
                "id": item.id,
                "category": item.category,
                "sub_category": item.sub_category,
                "color": item.color,
                "style": item.style,
                "ai_description": item.ai_description,
            }
            for item in items
        ]

        # 建立 ID → 衣物 的映射
        items_map = {item.id: item for item in items}

        # 调用 AI 推荐
        ai_outfits = await recommend_outfits(wardrobe_data)

        # 处理每套搭配：存库 + 生成卡片
        outfit_responses = []
        for ai_outfit in ai_outfits:
            item_ids = ai_outfit.get("item_ids", [])
            style_tags = ai_outfit.get("style_tags", [])
            description = ai_outfit.get("description", "")
            reason = ai_outfit.get("reason", "")

            # 收集搭配中的衣物信息
            outfit_items_detail = []
            card_items = []
            for iid in item_ids:
                if iid in items_map:
                    ci = items_map[iid]
                    outfit_items_detail.append(
                        OutfitItemDetail(
                            id=ci.id,
                            thumbnail_url=f"/static/{ci.thumbnail_url}" if ci.thumbnail_url else None,
                            category=ci.category,
                            color=ci.color,
                        )
                    )
                    card_items.append({
                        "thumbnail_url": ci.thumbnail_url or ci.image_url,
                        "image_url": ci.image_url,
                        "category": ci.category,
                        "color": ci.color,
                    })

            # 生成搭配卡片
            card_url = ""
            try:
                card_url = generate_outfit_card(
                    items=card_items,
                    description=description,
                    style_tags=style_tags,
                    reason=reason,
                )
            except Exception as e:
                logger.error(f"搭配卡片生成失败: {e}")

            # 存入数据库
            outfit = Outfit(
                user_id=user.id,
                item_ids=",".join(str(i) for i in item_ids),
                description=description,
                style_tags=",".join(style_tags),
                reason=reason,
                card_url=card_url,
            )
            session.add(outfit)
            session.commit()
            session.refresh(outfit)

            outfit_responses.append(
                OutfitResponse(
                    id=outfit.id,
                    items=outfit_items_detail,
                    description=description,
                    style_tags=style_tags,
                    reason=reason,
                    card_url=f"/static/{card_url}" if card_url else None,
                    created_at=outfit.created_at,
                )
            )

        return RecommendResponse(outfits=outfit_responses)


# ============ 健康检查 ============

@app.get("/api/health", summary="健康检查")
async def health_check():
    return {
        "status": "ok",
        "service": "StyleMate 搭搭",
        "version": "0.1.0",
    }


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,  # 开发模式热重载
        log_level="info",
    )
