#!/bin/bash
# 大肥鱼 AI 伴侣 - 一键启动 (Termux / Linux)

set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  大肥鱼 AI 伴侣 - 一键启动"
echo "============================================================"

# 检查 .env
if [ ! -f ".env" ]; then
    cp bigfatfish/config/example.env .env
    echo "[!] 已生成 .env，请先填 DEEPSEEK_API_KEY"
    exit 1
fi

# 首次运行自动装轻量依赖
if ! python -c "import aiohttp, websockets" 2>/dev/null; then
    echo "[1/3] 首次运行，正在安装依赖..."
    pip install -r requirements-lite.txt
else
    echo "[1/3] 依赖已就绪"
fi

# 启动 Redis（有就起，没有程序会自己降级）
if command -v redis-server >/dev/null 2>&1; then
    if ! pgrep -x "redis-server" >/dev/null; then
        echo "[2/3] 启动 Redis..."
        redis-server --daemonize yes --dir ./data/redis --save 300 1 2>/dev/null || true
    fi
else
    echo "[2/3] 未装 Redis，自动使用内存缓存"
fi

echo "[3/3] 启动服务..."
echo "   QQ 端口  : 3001"
echo "   界面地址 : http://127.0.0.1:8080"
echo ""

python -m bigfatfish.main
