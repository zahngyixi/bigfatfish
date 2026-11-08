@echo off
REM ============================================================
REM 大肥鱼 AI 伴侣 - Windows 一键部署脚本
REM ============================================================
REM 使用方法: 双击运行 deploy.bat
REM ============================================================

echo 🐟 大肥鱼 AI 伴侣 - 开始部署 (Windows)
echo ============================================================

REM ==================== 检查 Python ====================
echo.
echo 🐍 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo ✓ Python 已安装

REM ==================== 升级 pip ====================
echo.
echo 📦 升级 pip...
python -m pip install --upgrade pip

REM ==================== 安装依赖 ====================
echo.
echo 📦 安装 Python 依赖...
pip install -r requirements.txt

echo ✓ Python 依赖安装完成

REM ==================== 配置环境变量 ====================
echo.
echo ⚙️ 配置环境变量...

if not exist ".env" (
    if exist "bigfatfish\config\example.env" (
        copy bigfatfish\config\example.env .env
        echo ✓ 已创建 .env 文件，请编辑配置
        echo    必需配置项: DEEPSEEK_API_KEY
    )
) else (
    echo ✓ .env 文件已存在
)

REM ==================== 创建启动脚本 ====================
echo.
echo 📝 创建启动脚本...

echo @echo off > start.bat
echo python -m bigfatfish.main >> start.bat
echo pause >> start.bat

echo ✓ 启动脚本已创建: start.bat

REM ==================== 部署完成 ====================
echo.
echo ============================================================
echo 🎉 大肥鱼 AI 伴侣 部署完成！
echo ============================================================
echo.
echo 📋 后续步骤:
echo    1. 编辑配置文件: .env
echo       必须配置 DEEPSEEK_API_KEY
echo.
echo    2. 如果需要 Redis，请安装 Redis for Windows
echo       或禁用 Redis（程序会自动切换到内存缓存）
echo.
echo    3. 启动程序: 双击 start.bat
echo.
echo ============================================================
pause
