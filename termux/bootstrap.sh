#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# 大肥鱼 AI 伴侣 - Termux 一键安装引导脚本
# ============================================================
# 用法：在 Termux 里执行
#   curl -fsSL https://你的仓库地址/raw/main/termux/bootstrap.sh | bash
# 或下载后执行：bash bootstrap.sh
# ============================================================

set -e

echo "🐟 大肥鱼 AI 伴侣 - Termux 一键安装"
echo "============================================================"
echo ""

# 检测 Termux 环境
if [[ ! "$PREFIX" =~ "com.termux" ]]; then
    echo "❌ 请在 Termux 环境中运行此脚本"
    exit 1
fi

echo "✓ Termux 环境检测通过"
echo ""

# 安装系统依赖
echo "📦 更新 Termux 软件源并安装依赖..."
pkg update -y
pkg upgrade -y
pkg install -y python python-pip git rust clang cmake ffmpeg espeak redis

echo "✓ 系统依赖安装完成"
echo ""

# 克隆项目（如果还没有）
if [ ! -d "$HOME/bigfatfish" ]; then
    echo "📥 克隆项目到 ~/bigfatfish ..."
    cd "$HOME"
    git clone https://github.com/你的用户名/bigfatfish.git
    cd bigfatfish
else
    echo "✓ 项目目录已存在，更新代码..."
    cd "$HOME/bigfatfish"
    git pull
fi

echo "✓ 项目代码已就绪"
echo ""

# 安装 Python 依赖
echo "📦 安装 Python 依赖（这可能需要 5-10 分钟）..."
pip install -r requirements.txt

echo "✓ Python 依赖安装完成"
echo ""

# 下载 sherpa-onnx 模型（可选）
if [ ! -d "models/sherpa-onnx/encoder-epoch-12.onnx" ]; then
    echo "🎤 下载 sherpa-onnx 中文语音识别模型（约 50MB）..."
    mkdir -p models
    cd models
    
    if command -v wget &> /dev/null; then
        wget "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2" -O model.tar.bz2
    elif command -v curl &> /dev/null; then
        curl -L "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2" -o model.tar.bz2
    else
        echo "⚠ 未找到 wget 或 curl，跳过模型下载"
        cd ..
        echo "   如需语音识别，请手动下载模型到 models/sherpa-onnx/"
    fi
    
    if [ -f "model.tar.bz2" ]; then
        tar -xjf model.tar.bz2
        mv sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23/* sherpa-onnx/
        rm -rf model.tar.bz2 sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
        echo "✓ 模型下载完成"
    fi
    
    cd ..
fi

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "⚙️ 生成配置文件 .env ..."
    cp bigfatfish/config/example.env .env
    echo ""
    echo "⚠ 请编辑 .env 文件，配置你的 DeepSeek API Key："
    echo "   nano .env"
    echo ""
    echo "必需配置项："
    echo "   - DEEPSEEK_API_KEY=sk-xxxxx"
    echo "   - QQ_BOT_QQ=你的机器人QQ号"
else
    echo "✓ 配置文件 .env 已存在"
fi

# 启动 Redis
echo ""
echo "🗄️ 启动 Redis 服务..."
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ./data/redis --save 300 1
    echo "✓ Redis 已启动"
else
    echo "✓ Redis 已在运行"
fi

# 创建 Termux Widget 快捷方式
echo ""
echo "📱 创建桌面快捷方式..."
mkdir -p "$HOME/.shortcuts"

cat > "$HOME/.shortcuts/启动大肥鱼" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/bigfatfish
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ./data/redis --save 300 1
fi
python -m bigfatfish.main
EOF

chmod +x "$HOME/.shortcuts/启动大肥鱼"

cat > "$HOME/.shortcuts/停止大肥鱼" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "bigfatfish.main"
echo "✓ 大肥鱼已停止"
EOF

chmod +x "$HOME/.shortcuts/停止大肥鱼"

echo "✓ 快捷方式已创建（需要安装 Termux:Widget 才能在桌面显示）"
echo ""

# 配置开机自启（需要 Termux:Boot）
mkdir -p "$HOME/.termux/boot"

cat > "$HOME/.termux/boot/bigfatfish-boot.sh" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
sleep 10
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes --dir ~/bigfatfish/data/redis --save 300 1
fi
cd ~/bigfatfish
python -m bigfatfish.main > ~/bigfatfish-boot.log 2>&1 &
EOF

chmod +x "$HOME/.termux/boot/bigfatfish-boot.sh"

echo "✓ 开机自启已配置（需要安装 Termux:Boot）"
echo ""

# 完成
echo "============================================================"
echo "🎉 大肥鱼 AI 伴侣 安装完成！"
echo "============================================================"
echo ""
echo "📋 后续步骤："
echo ""
echo "1. 编辑配置文件："
echo "   nano .env"
echo "   必须配置 DEEPSEEK_API_KEY"
echo ""
echo "2. 如果接入 QQ，需要先在另一台设备运行 NapCatQQ 或 Lagrange"
echo "   参考文档: QQ_SETUP_GUIDE.md"
echo ""
echo "3. 启动大肥鱼："
echo "   python -m bigfatfish.main"
echo ""
echo "4. 手机浏览器访问 Web UI："
echo "   程序启动后会显示二维码，扫码即可访问"
echo ""
echo "5. 桌面快捷方式（需要安装 Termux:Widget）："
echo "   长按桌面 → 小部件 → Termux:Widget → 选择「启动大肥鱼」"
echo ""
echo "============================================================"
echo "📚 文档："
echo "   - README.md       : 完整项目文档"
echo "   - QQ_SETUP_GUIDE.md : QQ 接入指南"
echo "   - PACKAGING.md    : 打包方案对比"
echo "============================================================"
