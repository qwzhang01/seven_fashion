"""
图片处理服务
- 抠图：使用 rembg 去除背景
- 搭配卡片：使用 Pillow 生成精美搭配卡片
"""

import logging
import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config

logger = logging.getLogger(__name__)

# rembg 延迟导入（首次加载模型较慢）
_rembg_session = None


def _get_rembg_session():
    """延迟初始化 rembg session"""
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session
        _rembg_session = new_session("u2net")
    return _rembg_session


# ============ 图片保存 & 压缩 ============

def save_upload_image(image_bytes: bytes, original_filename: str) -> str:
    """
    保存上传的图片，压缩到合理尺寸

    Returns:
        保存后的相对路径（如 uploads/xxx.jpg）
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        ext = ".jpg"

    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = config.UPLOAD_DIR / filename

    # 打开、压缩、保存
    img = Image.open(BytesIO(image_bytes))

    # 转 RGB（处理 RGBA/HEIC 等格式）
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        save_path = config.UPLOAD_DIR / filename

    # 限制最大尺寸，节省存储和 AI 调用成本
    max_size = 1024
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    img.save(save_path, quality=85, optimize=True)
    logger.info(f"保存上传图片: {save_path}, 尺寸: {img.size}")

    return f"uploads/{filename}"


# ============ 抠图 ============

def remove_background(image_path: str) -> str:
    """
    使用 rembg 去除衣物背景

    Args:
        image_path: 原图的相对路径（如 uploads/xxx.jpg）

    Returns:
        抠图后的相对路径（如 processed/xxx.png）
    """
    full_path = config.BASE_DIR / image_path
    if not full_path.exists():
        raise FileNotFoundError(f"图片不存在: {full_path}")

    try:
        from rembg import remove

        input_image = Image.open(full_path)
        session = _get_rembg_session()
        output_image = remove(input_image, session=session)

        # 裁剪到内容区域（去除多余透明边缘）
        bbox = output_image.getbbox()
        if bbox:
            output_image = output_image.crop(bbox)

        # 调整大小
        output_image.thumbnail(config.THUMBNAIL_SIZE, Image.LANCZOS)

        # 保存为 PNG（保留透明背景）
        filename = f"{uuid.uuid4().hex}.png"
        save_path = config.PROCESSED_DIR / filename
        output_image.save(save_path, "PNG")

        logger.info(f"抠图完成: {save_path}, 尺寸: {output_image.size}")
        return f"processed/{filename}"

    except Exception as e:
        logger.error(f"抠图失败: {e}")
        # 抠图失败就用原图
        return image_path


# ============ 搭配卡片生成 ============

def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """获取字体，优先系统中文字体"""
    font_paths = [
        # macOS 中文字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux 中文字体
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        # 项目自带字体
        str(config.FONTS_DIR / "font.ttf"),
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw: ImageDraw.Draw, xy: tuple, radius: int, fill: str):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def generate_outfit_card(
    items: list[dict],
    description: str,
    style_tags: list[str],
    reason: str = "",
) -> str:
    """
    生成搭配卡片图

    Args:
        items: 衣物列表，每个元素包含 {thumbnail_url, category, color}
        description: AI 搭配说明
        style_tags: 风格标签列表
        reason: 搭配理由

    Returns:
        卡片图的相对路径（如 cards/xxx.png）

    卡片布局（800 x 自适应高度）：
    ┌────────────────────────────┐
    │    ✨ 今日穿搭推荐           │  标题区
    ├────────────────────────────┤
    │  ┌──────┐  ┌──────┐       │
    │  │ 衣物1 │  │ 衣物2 │       │  衣物拼图区
    │  └──────┘  └──────┘       │
    │       ┌──────┐            │
    │       │ 衣物3 │            │
    │       └──────┘            │
    ├────────────────────────────┤
    │  #标签1  #标签2            │  标签区
    │  搭配说明文字...           │  说明区
    ├────────────────────────────┤
    │  搭搭 StyleMate 💫        │  水印区
    └────────────────────────────┘
    """
    card_width = config.CARD_WIDTH
    padding = 40
    content_width = card_width - padding * 2

    # ============ 准备衣物图片 ============
    item_images = []
    for item in items:
        thumb_path = item.get("thumbnail_url") or item.get("image_url", "")
        full_path = config.BASE_DIR / thumb_path
        if full_path.exists():
            try:
                img = Image.open(full_path)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                item_images.append({"img": img, "category": item.get("category", "")})
            except Exception as e:
                logger.warning(f"加载衣物图片失败: {e}")

    # ============ 计算布局尺寸 ============
    # 衣物图片区域：根据数量自适应
    item_area_height = 400
    if len(item_images) <= 2:
        item_area_height = 300
    elif len(item_images) >= 4:
        item_area_height = 500

    # 文字区域高度估算
    text_area_height = 200

    card_height = 80 + item_area_height + text_area_height + 60  # 标题 + 图片 + 文字 + 水印

    # ============ 创建画布 ============
    card = Image.new("RGB", (card_width, card_height), config.CARD_BG_COLOR)
    draw = ImageDraw.Draw(card)

    # ============ 1. 标题区 ============
    title_font = _get_font(28)
    title_text = "✨ 今日穿搭推荐"
    draw.text((padding, 25), title_text, fill="#333333", font=title_font)

    # 分割线
    line_y = 65
    draw.line([(padding, line_y), (card_width - padding, line_y)], fill="#EEEEEE", width=2)

    # ============ 2. 衣物拼图区 ============
    items_start_y = 80
    if item_images:
        n = len(item_images)
        # 计算每张图的大小和位置
        if n == 1:
            cols, rows = 1, 1
        elif n == 2:
            cols, rows = 2, 1
        elif n <= 4:
            cols, rows = 2, 2
        else:
            cols, rows = 3, 2

        cell_w = content_width // cols
        cell_h = item_area_height // rows
        img_margin = 10

        for i, item_data in enumerate(item_images):
            row = i // cols
            col = i % cols
            if row >= rows:
                break

            img = item_data["img"]
            # 等比缩放到 cell 大小
            target_w = cell_w - img_margin * 2
            target_h = cell_h - img_margin * 2
            img.thumbnail((target_w, target_h), Image.LANCZOS)

            # 居中放置
            x = padding + col * cell_w + (cell_w - img.width) // 2
            y = items_start_y + row * cell_h + (cell_h - img.height) // 2

            # 绘制白色背景框
            bg_rect = (x - 8, y - 8, x + img.width + 8, y + img.height + 8)
            _draw_rounded_rect(draw, bg_rect, radius=12, fill="#FFFFFF")

            # 粘贴衣物图（处理透明通道）
            if img.mode == "RGBA":
                card.paste(img, (x, y), img)
            else:
                card.paste(img, (x, y))

            # 在图片下方标注品类
            cat_font = _get_font(14)
            cat_text = item_data["category"]
            cat_bbox = draw.textbbox((0, 0), cat_text, font=cat_font)
            cat_w = cat_bbox[2] - cat_bbox[0]
            draw.text(
                (x + (img.width - cat_w) // 2, y + img.height + 4),
                cat_text,
                fill="#999999",
                font=cat_font,
            )

    # ============ 3. 标签 & 说明区 ============
    text_y = items_start_y + item_area_height + 10

    # 分割线
    draw.line([(padding, text_y), (card_width - padding, text_y)], fill="#EEEEEE", width=2)
    text_y += 15

    # 风格标签
    tag_font = _get_font(18)
    if style_tags:
        tag_text = "  ".join([f"#{tag}" for tag in style_tags])
        draw.text((padding, text_y), tag_text, fill=config.CARD_ACCENT_COLOR, font=tag_font)
        text_y += 35

    # 搭配说明
    desc_font = _get_font(20)
    # 简单的文字换行
    max_chars_per_line = content_width // 20  # 粗略估算
    lines = []
    current_line = ""
    for char in description:
        current_line += char
        if len(current_line) >= max_chars_per_line:
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)

    for line in lines[:3]:  # 最多 3 行
        draw.text((padding, text_y), line, fill="#333333", font=desc_font)
        text_y += 30

    # 搭配理由
    if reason:
        text_y += 5
        reason_font = _get_font(16)
        draw.text((padding, text_y), f"💡 {reason}", fill="#888888", font=reason_font)
        text_y += 30

    # ============ 4. 水印区 ============
    text_y += 10
    draw.line([(padding, text_y), (card_width - padding, text_y)], fill="#EEEEEE", width=1)
    watermark_font = _get_font(16)
    draw.text((padding, text_y + 10), "搭搭 StyleMate 💫", fill="#CCCCCC", font=watermark_font)

    # ============ 裁剪到实际内容高度 ============
    final_height = text_y + 45
    if final_height < card_height:
        card = card.crop((0, 0, card_width, final_height))

    # ============ 保存 ============
    filename = f"{uuid.uuid4().hex}.png"
    save_path = config.CARDS_DIR / filename
    card.save(save_path, "PNG", quality=95)
    logger.info(f"搭配卡片生成: {save_path}")

    return f"cards/{filename}"
