#!/data/data/com.termux/files/usr/bin/bash
# Termux:Widget 桌面快捷方式 - 启动大肥鱼

cd ~/bigfatfish

# 启动 Redis（如果未运行）
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ./data/redis --save 300 1
    echo "✓ Redis 已启动"
fi

# 启动大肥鱼
echo "🐟 正在启动大肥鱼 AI 伴侣..."
python -m bigfatfish.main
