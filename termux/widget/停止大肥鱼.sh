#!/data/data/com.termux/files/usr/bin/bash
# Termux:Widget 桌面快捷方式 - 停止大肥鱼

pkill -f "bigfatfish.main"

echo "✓ 大肥鱼已停止"

# 可选：同时停止 Redis
# redis-cli shutdown
