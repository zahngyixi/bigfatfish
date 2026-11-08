#!/bin/bash
# ============================================================
# 大肥鱼 AI 伴侣 - Termux/Linux 一键部署脚本
# ============================================================
# 目标环境: Android Termux (ARM64)
# 使用方法: bash deploy.sh
# ============================================================

set -e  # 遇到错误立即退出

echo "🐟 大肥鱼 AI 伴侣 - 开始部署 (Termux ARM64)"
echo "============================================================"

# ==================== 检测环境 ====================
if [[ "$OSTYPE" == "linux-android"* ]]; then
    echo "✓ 检测到 Termux 环境"
    IS_TERMUX=true
else
    echo "✓ 检测到 Linux 环境"
    IS_TERMUX=false
fi

# ==================== 安装系统依赖 (Termux) ====================
if [ "$IS_TERMUX" = true ]; then
    echo ""
    echo "📦 安装 Termux 系统依赖..."
    pkg update -y
    pkg install -y python python-pip
    pkg install -y rust clang cmake  # chromadb 编译依赖
    pkg install -y ffmpeg            # 音频处理
    pkg install -y espeak            # pyttsx3 TTS
    pkg install -y redis             # Redis 服务器
    pkg install -y git               # 版本控制
    
    echo "✓ Termux 系统依赖安装完成"
fi

# ==================== 检查 Python 版本 ====================
echo ""
echo "🐍 检查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $PYTHON_VERSION"

# 版本要求 >= 3.10
REQUIRED_VERSION="3.10"
if python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "✓ Python 版本满足要求"
else
    echo "❌ Python 版本过低 (需要 >= 3.10)"
    echo "请升级 Python: pkg install python"
    exit 1
fi

# ==================== 升级 pip ====================
echo ""
echo "📦 升级 pip..."
python -m pip install --upgrade pip

# ==================== 安装 Python 依赖 ====================
echo ""
echo "📦 安装 Python 依赖 (ARM64 兼容版本)..."
echo "这可能需要 5-10 分钟，请耐心等待..."

# 优先安装 wheel 和 setuptools
pip install wheel setuptools

# 安装核心依赖
pip install -r requirements.txt

echo "✓ Python 依赖安装完成"

# ==================== 下载 sherpa-onnx ASR 模型 ====================
echo ""
echo "🎤 下载 sherpa-onnx 中文语音识别模型..."

MODEL_DIR="./models/sherpa-onnx"
MODEL_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2"

if [ ! -d "$MODEL_DIR" ]; then
    mkdir -p "$MODEL_DIR"
    
    echo "正在下载模型 (约 50MB)..."
    cd models
    
    if command -v wget &> /dev/null; then
        wget "$MODEL_URL" -O model.tar.bz2
    elif command -v curl &> /dev/null; then
        curl -L "$MODEL_URL" -o model.tar.bz2
    else
        echo "❌ 未找到 wget 或 curl，请手动下载模型:"
        echo "   $MODEL_URL"
        echo "   解压到: $MODEL_DIR"
        cd ..
        exit 1
    fi
    
    echo "正在解压模型..."
    tar -xjf model.tar.bz2
    mv sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23/* sherpa-onnx/
    rm -rf model.tar.bz2 sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
    
    cd ..
    echo "✓ 模型下载完成"
else
    echo "✓ 模型目录已存在，跳过下载"
fi

# ==================== 配置环境变量 ====================
echo ""
echo "⚙️ 配置环境变量..."

if [ ! -f ".env" ]; then
    if [ -f "bigfatfish/config/example.env" ]; then
        cp bigfatfish/config/example.env .env
        echo "✓ 已创建 .env 文件，请编辑配置:"
        echo "   nano .env"
        echo ""
        echo "必需配置项:"
        echo "   - DEEPSEEK_API_KEY=your_api_key_here"
        echo "   - QQ_WS_MODE=reverse (大肥鱼监听 3001，NapCat 连过来)"
        echo "   - QQ_WEBSOCKET_URL=ws://0.0.0.0:3001"
        echo "   - QQ_BOT_QQ=你的机器人QQ号"
    fi
else
    echo "✓ .env 文件已存在"
fi

# ==================== 启动 Redis (可选) ====================
echo ""
echo "🗄️ 启动 Redis 服务器 (短期记忆)..."

if [ "$IS_TERMUX" = true ]; then
    # Termux 中后台启动 Redis
    if ! pgrep -x "redis-server" > /dev/null; then
        redis-server --daemonize yes --dir ./data/redis --save 300 1
        echo "✓ Redis 已启动"
    else
        echo "✓ Redis 已在运行"
    fi
fi

# ==================== 创建启动脚本 ====================
echo ""
echo "📝 创建启动脚本..."

cat > start.sh <<'EOF'
#!/bin/bash
# 大肥鱼 AI 伴侣 - 启动脚本

echo "🐟 正在启动大肥鱼 AI 伴侣..."

# 启动 Redis (如果未运行)
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ./data/redis --save 300 1
    echo "✓ Redis 已启动"
fi

# 启动主程序
python -m bigfatfish.main
EOF

chmod +x start.sh
echo "✓ 启动脚本已创建: ./start.sh"

# ==================== 部署完成 ====================
echo ""
echo "============================================================"
echo "🎉 大肥鱼 AI 伴侣 部署完成！"
echo "============================================================"
echo ""
echo "📋 后续步骤:"
echo "   1. 编辑配置文件: nano .env"
echo "      必须配置 DEEPSEEK_API_KEY"
echo ""
echo "   2. 如果接入 QQ，需要先启动 NapCatQQ 或 Lagrange"
echo "      配置反向 WebSocket: ws://<大肥鱼IP>:3001 (同机填 127.0.0.1)"
echo ""
echo "   3. 启动程序: ./start.sh"
echo "      或: python -m bigfatfish.main"
echo ""
echo "   4. 手机浏览器访问 Web UI:"
echo "      程序启动后会显示二维码，扫码即可访问"
echo ""
echo "============================================================"
echo "💡 提示:"
echo "   - 日志文件: bigfatfish/logs/bigfatfish.log"
echo "   - 停止程序: Ctrl+C"
echo "   - 重启 Redis: redis-cli shutdown && redis-server --daemonize yes"
echo "============================================================"
