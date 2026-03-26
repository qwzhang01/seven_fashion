# 🎨 StyleMate 搭搭 — AI 穿搭助手

> 拍照上传衣物 → AI 自动识别 → 智能生成搭配方案

**StyleMate 搭搭** 是一款基于微信小程序的 AI 穿搭助手，通过多模态大模型识别衣物属性，结合 LLM 生成个性化搭配方案，并自动生成精美搭配卡片。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📷 **拍照建衣橱** | 拍照/上传衣物照片，AI 自动识别类别、颜色、风格、季节 |
| ✂️ **智能抠图** | 使用 rembg 自动去除背景，生成干净的衣物缩略图 |
| 🤖 **AI 搭配推荐** | 基于衣橱中的衣物，AI 生成 3 套搭配方案 + 搭配理由 |
| 🖼️ **搭配卡片** | 自动生成精美搭配卡片图，可保存到相册分享 |
| 👤 **静默登录** | 微信小程序无感登录，零门槛使用 |

---

## 🏗️ 技术架构

```
┌───────────────────────────────┐
│     微信小程序（3 个页面）       │
│   首页/衣橱 · 上传 · 搭配结果   │
└──────────────┬────────────────┘
               │ HTTP
┌──────────────▼────────────────┐
│      Python FastAPI 后端       │
│      4 个 RESTful API 接口     │
└───┬──────────┬────────────────┘
    │          │
┌───▼───┐  ┌──▼───────────────┐
│SQLite │  │ AI 服务           │
│数据库  │  │ (OpenAI 兼容接口) │
└───────┘  └──────────────────┘
```

### 后端技术栈

- **框架**：FastAPI + Uvicorn
- **数据库**：SQLite + SQLModel
- **AI 模型**：OpenAI 兼容接口（支持豆包/通义千问/GPT-4o/DeepSeek 等）
- **图片处理**：rembg（抠图） + Pillow（卡片生成）
- **Python**：3.11+

### 小程序技术栈

- **框架**：微信小程序原生
- **页面**：首页（衣橱列表）、上传页、搭配结果页
- **组件**：clothing-card、outfit-card、empty-state

---

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传衣物照片 → AI 识别 → 抠图 → 入库 |
| `/api/wardrobe` | GET | 获取用户衣橱列表 |
| `/api/recommend` | POST | AI 搭配推荐（生成 3 套方案 + 搭配卡片） |
| `/api/health` | GET | 健康检查 |

启动后可访问 **http://localhost:8000/docs** 查看交互式 API 文档。

---

## 🚀 部署方式

### 方式一：本地开发

#### 1. 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境并安装依赖
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配置环境变量（复制模板并填写 AI 模型的 API Key）
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 启动服务
python app.py
```

服务默认运行在 `http://0.0.0.0:8000`。

#### 2. 小程序部署

1. 使用 **微信开发者工具** 打开 `miniprogram/` 目录
2. 修改 `miniprogram/utils/api.js` 中的 `BASE_URL`：
   - 模拟器调试：`http://localhost:8000`
   - 真机调试：`http://<你的局域网IP>:8000`（手机与电脑需在同一 Wi-Fi）
3. 在微信开发者工具中编译运行

### 方式二：Docker 部署

```bash
cd backend

# 构建镜像
docker build -t stylemate .

# 运行容器
docker run -d \
  --name stylemate \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/processed:/app/processed \
  -v $(pwd)/cards:/app/cards \
  --env-file .env \
  stylemate
```

---

## ⚙️ 环境变量配置

在 `backend/.env` 中配置（参考 `.env.example`）：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `VISION_MODEL_BASE_URL` | 多模态模型 API 地址 | `https://ark.cn-beijing.volces.com/api/v3` |
| `VISION_MODEL_API_KEY` | 多模态模型 API Key | `sk-xxx` |
| `VISION_MODEL_NAME` | 多模态模型名称 | `doubao-seed-2-0-pro-260215` |
| `LLM_BASE_URL` | LLM 模型 API 地址 | `https://api.deepseek.com/v1` |
| `LLM_API_KEY` | LLM 模型 API Key | `sk-xxx` |
| `LLM_MODEL_NAME` | LLM 模型名称 | `deepseek-chat` |
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |

支持的 AI 模型方案：
- **豆包**（字节跳动火山引擎）— 推荐，国内速度快
- **通义千问**（阿里云）— qwen-vl-plus / qwen-plus
- **GPT-4o**（OpenAI）— 效果最好
- **DeepSeek** — 性价比高

---

## 📁 项目结构

```
stylemate/
├── backend/                 # Python FastAPI 后端
│   ├── app.py              # 主应用 & API 路由
│   ├── ai_service.py       # AI 服务层（识别 + 推荐）
│   ├── image_service.py    # 图片处理（抠图 + 卡片生成）
│   ├── models.py           # 数据模型（SQLModel）
│   ├── config.py           # 配置管理
│   ├── requirements.txt    # Python 依赖
│   ├── Dockerfile          # Docker 构建文件
│   ├── .env.example        # 环境变量模板
│   └── static/fonts/       # 字体目录
├── miniprogram/            # 微信小程序前端
│   ├── pages/
│   │   ├── index/          # 首页（衣橱列表）
│   │   ├── upload/         # 上传衣物页
│   │   └── result/         # 搭配结果页
│   ├── components/
│   │   ├── clothing-card/  # 衣物卡片组件
│   │   ├── outfit-card/    # 搭配卡片组件
│   │   └── empty-state/    # 空状态组件
│   └── utils/
│       ├── api.js          # API 请求封装
│       └── util.js         # 工具函数
├── docs/                   # 项目文档
└── README.md
```

---

## 📝 License

本项目仅供学习交流使用。
