# 大肥鱼 AI 伴侣 - Docker 镜像
# 适用于 Render / Railway / Fly.io 等 PaaS 平台
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件并安装
COPY requirements-lite.txt .
RUN pip install --no-cache-dir -r requirements-lite.txt

# 复制项目文件
COPY bigfatfish ./bigfatfish
COPY .env.example .env

# 暴露端口
EXPOSE 8080 3001

# 启动命令
CMD ["python", "-m", "bigfatfish.main"]
