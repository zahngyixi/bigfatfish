@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   大肥鱼 AI 伴侣 - 一键启动
echo ============================================================
echo.

REM 首次运行自动装轻量依赖（免编译，约 1 分钟）
python -c "import aiohttp, websockets" >nul 2>&1
if errorlevel 1 (
    echo [1/2] 首次运行，正在安装依赖...
    python -m pip install -r requirements-lite.txt -q
) else (
    echo [1/2] 依赖已就绪
)

echo [2/2] 启动服务...
echo    QQ 端口  : 3001
echo    界面地址 : http://127.0.0.1:8080
echo    关闭服务 : 直接关掉这个窗口 / Ctrl+C
echo.

python -m bigfatfish.main

echo.
echo 服务已退出。
pause
