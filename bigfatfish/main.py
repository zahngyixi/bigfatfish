# -*- coding: utf-8 -*-
"""
大肥鱼 AI 伴侣 - 主程序入口
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 包路径兜底：无论从项目根目录还是 bigfatfish/ 目录启动都能正确 import
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

def _load_env_file(path: Path):
    """加载 .env；python-dotenv 缺失时用标准库兜底，保证极简环境也能读到配置"""
    try:
        from dotenv import load_dotenv
        load_dotenv(str(path))
        return
    except ImportError:
        pass
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# 依次查找 bigfatfish/.env → 各级上级目录的 .env
for _candidate in [Path(__file__).parent / ".env"] + [p / ".env" for p in Path(__file__).parents]:
    if _candidate.exists():
        _load_env_file(_candidate)
        break

# 设置日志（必须在其他导入之前）
from bigfatfish.utils.logger import setup_logging
logger = setup_logging()

# 核心模块
from bigfatfish.config import settings
from bigfatfish.core import DeepSeekAgent, MemoryManager
from bigfatfish.gateway import MessageRouter, QQAdapter, BilibiliAdapter
from bigfatfish.multimodal import TTSEngine, ASREngine, EmotionSystem, ImageGenerator
from bigfatfish.visual.ui_server import UIServer
from bigfatfish.scheduler import ActiveInteractionEngine


async def main():
    """主程序"""
    logger.info("🐟 大肥鱼 AI 伴侣 启动中...")
    
    # ========== 初始化记忆系统 ==========
    memory_manager = MemoryManager()
    
    # ========== 初始化 AI Agent ==========
    agent = DeepSeekAgent(memory_manager=memory_manager)
    
    # ========== 初始化多模态模块 ==========
    tts_engine = TTSEngine()
    asr_engine = ASREngine()
    emotion_system = EmotionSystem()
    image_generator = ImageGenerator()
    
    # ========== 初始化消息路由器 ==========
    router = MessageRouter()
    router.set_agent(agent)
    router.set_emotion_system(emotion_system)
    router.set_tts_engine(tts_engine)
    
    # ========== 注册平台适配器 ==========
    tasks = []
    
    if settings.QQ_ENABLED:
        qq_adapter = QQAdapter(router)
        tasks.append(asyncio.create_task(qq_adapter.start()))
    
    if settings.BILIBILI_ENABLED:
        bili_adapter = BilibiliAdapter(router)
        tasks.append(asyncio.create_task(bili_adapter.start()))
    
    # ========== 启动 Web UI ==========
    ui_server = UIServer(router=router)
    tasks.append(asyncio.create_task(ui_server.start()))
    
    # ========== 启动主动交互引擎 ==========
    active_engine = ActiveInteractionEngine(router=router, agent=agent)
    tasks.append(asyncio.create_task(active_engine.start()))
    
    logger.info("🎉 大肥鱼 AI 伴侣 启动完成！")
    
    # 等待所有任务
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        logger.info("👋 正在退出...")
    finally:
        await ui_server.stop()
        logger.info("✓ 大肥鱼 AI 伴侣 已停止")


if __name__ == "__main__":
    # 设置事件循环策略（Windows 兼容）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
