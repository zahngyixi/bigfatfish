#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot 开机自启脚本
# 需要先安装 Termux:Boot: https://f-droid.org/packages/com.termux.boot/

# 等待系统完全启动
sleep 10

# 启动 Redis
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ~/bigfatfish/data/redis --save 300 1
fi

# 启动大肥鱼（后台运行，日志输出到 ~/bigfatfish-boot.log）
cd ~/bigfatfish
python -m bigfatfish.main > ~/bigfatfish-boot.log 2>&1 &
