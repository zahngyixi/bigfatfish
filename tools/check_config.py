# -*- coding: utf-8 -*-
"""
大肥鱼 AI 伴侣 - 配置就绪自检
用法: python tools/check_config.py

只检查「能不能跑起来」，不联网、不调用 API、不启动服务。
退出码: 0 = 必需项全部就绪, 1 = 有阻塞项
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

OK = "[OK]  "
WARN = "[WARN]"
BAD = "[BAD] "

blocks = []
warns = []


def load_env(path: Path) -> dict:
    """极简 .env 解析（不依赖 python-dotenv）"""
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    return cfg


def main():
    print("=" * 58)
    print(" 大肥鱼 AI 伴侣 - 配置就绪自检")
    print("=" * 58)

    # ---------- 1. .env ----------
    if not ENV_FILE.exists():
        print(f"{BAD} .env 不存在")
        print("      -> 复制模板: cp bigfatfish/config/example.env .env")
        print("         Windows : copy bigfatfish\\config\\example.env .env")
        blocks.append(".env")
        cfg = {}
    else:
        cfg = load_env(ENV_FILE)
        print(f"{OK} .env 已找到 ({ENV_FILE})")

    # ---------- 2. DeepSeek API Key ----------
    key = os.getenv("DEEPSEEK_API_KEY") or cfg.get("DEEPSEEK_API_KEY", "")
    if not key or key.startswith("your_") or key == "sk-xxxxx":
        print(f"{BAD} DEEPSEEK_API_KEY 未填写")
        print("      -> 到 https://platform.deepseek.com 申请，填进 .env")
        blocks.append("DEEPSEEK_API_KEY")
    else:
        masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"{OK} DEEPSEEK_API_KEY = {masked}")

    # ---------- 3. QQ ----------
    qq_on = (os.getenv("QQ_ENABLED") or cfg.get("QQ_ENABLED", "true")).lower() == "true"
    if qq_on:
        mode = (os.getenv("QQ_WS_MODE") or cfg.get("QQ_WS_MODE", "reverse")).lower()
        ws_url = os.getenv("QQ_WEBSOCKET_URL") or cfg.get("QQ_WEBSOCKET_URL", "ws://0.0.0.0:3001")
        bot_qq = os.getenv("QQ_BOT_QQ") or cfg.get("QQ_BOT_QQ", "")
        print(f"{OK} QQ_ENABLED = true  (模式: {mode})")
        print(f"{OK} QQ_WEBSOCKET_URL = {ws_url}")
        if mode == "reverse" and "0.0.0.0" not in ws_url and "127.0.0.1" not in ws_url:
            print(f"{WARN} reverse 模式下这应是「监听地址」，建议 ws://0.0.0.0:3001")
            warns.append("ws_url")
        if not bot_qq or bot_qq == "123456789":
            print(f"{WARN} QQ_BOT_QQ 未填/仍是示例值（群聊 @ 可能不触发）")
            print("      -> 反向 WS 下程序会尝试从 X-Self-ID 自动识别")
            warns.append("bot_qq")
        else:
            print(f"{OK} QQ_BOT_QQ = {bot_qq}")
        print("      提示: NapCat 侧填 reverse.ws.urls = ws://<本机IP>:3001")
        print("             启动顺序 = 先大肥鱼(服务端) -> 再 NapCat")
    else:
        print(f"{OK} QQ_ENABLED = false (仅 Web UI 模式)")

    # ---------- 4. Web UI ----------
    port = os.getenv("WEB_UI_PORT") or cfg.get("WEB_UI_PORT", "8080")
    print(f"{OK} Web UI 端口 = {port}  -> http://127.0.0.1:{port}")

    # ---------- 5. 关键文件 ----------
    required = [
        "bigfatfish/main.py",
        "bigfatfish/visual/assets/web/index.html",
        "bigfatfish/config/example.env",
        "requirements.txt",
    ]
    missing = [f for f in required if not (ROOT / f).exists()]
    if missing:
        for f in missing:
            print(f"{BAD} 缺文件: {f}")
        blocks.extend(missing)
    else:
        print(f"{OK} 关键文件齐全 ({len(required)} 项)")

    # ---------- 6. 依赖（软检查） ----------
    try:
        import aiohttp  # noqa: F401
        print(f"{OK} aiohttp 已安装")
    except ImportError:
        print(f"{BAD} aiohttp 未安装 -> pip install -r requirements.txt")
        blocks.append("pip install")

    for mod, label, optional in [
        ("websockets", "QQ 适配器", True),
        ("edge_tts", "语音合成", True),
        ("redis", "短期记忆", True),
        ("chromadb", "长期记忆", True),
    ]:
        try:
            __import__(mod)
            print(f"{OK} {label} ({mod}) 可用")
        except ImportError:
            level = WARN if optional else BAD
            print(f"{level} {label} ({mod}) 未安装" + ("，功能会降级" if optional else ""))
            if optional:
                warns.append(mod)

    # ---------- 汇总 ----------
    print("=" * 58)
    if blocks:
        print(f"[FAIL] 有 {len(blocks)} 个阻塞项，先处理再启动：")
        for b in blocks:
            print("   - " + b)
        print()
        print("处理完后重新运行: python tools/check_config.py")
        sys.exit(1)

    print("[PASS] 必需项全部就绪，可以启动了：")
    print("   python -m bigfatfish.main")
    if warns:
        print(f"       (另有 {len(warns)} 个非阻塞提醒，见上方 [WARN])")
    sys.exit(0)


if __name__ == "__main__":
    main()
