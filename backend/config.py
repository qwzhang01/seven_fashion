"""
StyleMate 配置文件
"""

import os
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# ============ 基础路径 ============
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
CARDS_DIR = BASE_DIR / "cards"
STATIC_DIR = BASE_DIR / "static"
FONTS_DIR = STATIC_DIR / "fonts"
DB_PATH = BASE_DIR / "stylemate.db"

# 确保目录存在
for d in [UPLOAD_DIR, PROCESSED_DIR, CARDS_DIR, STATIC_DIR, FONTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============ 数据库 ============
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ============ AI 配置 ============
# 支持多种模型，优先使用 OpenAI 兼容接口（通义千问/DeepSeek/GPT 都支持）

# 衣物识别模型（需要多模态能力）
VISION_MODEL_BASE_URL = os.getenv("VISION_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VISION_MODEL_API_KEY = os.getenv("VISION_MODEL_API_KEY", "")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen-vl-plus")

# 搭配推荐模型（纯文本 LLM）
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "deepseek-chat")

# ============ 图片处理 ============
MAX_IMAGE_SIZE = 4 * 1024 * 1024  # 4MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
THUMBNAIL_SIZE = (512, 512)  # 缩略图尺寸

# ============ 搭配卡片 ============
CARD_WIDTH = 800
CARD_HEIGHT = 1200
CARD_BG_COLOR = "#FAFAFA"
CARD_ACCENT_COLOR = "#FF6B6B"

# ============ 服务端口 ============
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
