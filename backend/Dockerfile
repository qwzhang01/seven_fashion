FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（Pillow 和 rembg 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 预下载 rembg 模型（避免首次请求慢）
RUN python -c "from rembg import new_session; new_session('u2net')"

# 复制代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads processed cards static/fonts

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
