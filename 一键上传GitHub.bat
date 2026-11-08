@echo off
chcp 65001 >nul
echo ============================================================
echo   大肥鱼 - GitHub 一键上传脚本
echo   你的 GitHub 用户名: zahngyixi
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] 检查 Git 是否安装...
where git >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Git，正在打开下载页面...
    start https://git-scm.com/download/win
    echo 安装完成后，重新运行此脚本。
    pause
    exit /b 1
)
echo [OK] Git 已安装

echo.
echo [2/5] 初始化 Git 仓库...
if not exist ".git" (
    git init
    git branch -M main
) else (
    echo [OK] 仓库已初始化
)

echo.
echo [3/5] 添加所有文件...
git add .

echo.
echo [4/5] 提交更改...
git commit -m "大肥鱼 AI 伴侣 - 初始部署 (鲸鱼娘人格)" 2>nul
if errorlevel 1 (
    echo [提示] 没有新的更改需要提交
)

echo.
echo [5/5] 推送到 GitHub...
echo [重要] 如果是第一次推送，需要你在浏览器里授权一次
echo.

git remote remove origin 2>nul
git remote add origin https://github.com/zahngyixi/bigfatfish.git
git push -u origin main

echo.
echo ============================================================
if errorlevel 1 (
    echo [失败] 推送失败，可能的原因：
    echo   1. 仓库还没创建 → 去 https://github.com/new 创建 bigfatfish
    echo   2. 需要登录 → Git 会弹窗，用浏览器授权
    echo   3. 网络问题 → 检查能否访问 github.com
    echo.
    echo 修复后，再次运行此脚本即可。
) else (
    echo [成功] 代码已上传到:
    echo   https://github.com/zahngyixi/bigfatfish
    echo.
    echo [下一步] 去 Render 部署（见下方说明）
)
echo ============================================================
echo.
pause
