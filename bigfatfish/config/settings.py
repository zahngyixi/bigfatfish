# -*- coding: utf-8 -*-
"""
全局配置管理
支持从环境变量和 .env 文件加载配置
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.parent


@dataclass
class Settings:
    """全局配置类"""
    
    # ========== DeepSeek API 配置 ==========
    DEEPSEEK_API_KEY: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    DEEPSEEK_API_BASE: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"))
    DEEPSEEK_MODEL: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    DEEPSEEK_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000")))
    DEEPSEEK_TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("DEEPSEEK_TEMPERATURE", "0.85")))
    DEEPSEEK_STREAM: bool = field(default_factory=lambda: os.getenv("DEEPSEEK_STREAM", "true").lower() == "true")
    
    # ========== 记忆系统配置 ==========
    # Redis 短期记忆
    REDIS_HOST: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    REDIS_PORT: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT") or "6379"))
    REDIS_DB: int = field(default_factory=lambda: int(os.getenv("REDIS_DB") or "0"))
    REDIS_PASSWORD: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    
    # ChromaDB 长期记忆
    CHROMADB_PATH: str = field(default_factory=lambda: os.getenv("CHROMADB_PATH", str(BASE_DIR / "data" / "chromadb")))
    CHROMADB_COLLECTION: str = field(default_factory=lambda: os.getenv("CHROMADB_COLLECTION", "bigfatfish_memory"))
    
    # 记忆参数
    SHORT_MEMORY_WINDOW: int = field(default_factory=lambda: int(os.getenv("SHORT_MEMORY_WINDOW", "10")))  # 短期记忆轮数
    LONG_MEMORY_TOP_K: int = field(default_factory=lambda: int(os.getenv("LONG_MEMORY_TOP_K", "5")))  # 长期记忆检索数量
    MEMORY_EXTRACT_INTERVAL: int = field(default_factory=lambda: int(os.getenv("MEMORY_EXTRACT_INTERVAL", "5")))  # 每 N 轮提取一次长期记忆
    
    # ========== 平台接入配置 ==========
    # QQ (NapCat/OneBot v11)
    QQ_ENABLED: bool = field(default_factory=lambda: os.getenv("QQ_ENABLED", "true").lower() == "true")
    QQ_WS_MODE: str = field(default_factory=lambda: os.getenv("QQ_WS_MODE", "reverse").lower())
    QQ_WEBSOCKET_URL: str = field(default_factory=lambda: os.getenv("QQ_WEBSOCKET_URL", "ws://0.0.0.0:3001"))
    QQ_HTTP_URL: str = field(default_factory=lambda: os.getenv("QQ_HTTP_URL", "http://localhost:3000"))
    QQ_BOT_QQ: str = field(default_factory=lambda: os.getenv("QQ_BOT_QQ", ""))
    QQ_ADMIN_LIST: list = field(default_factory=lambda: [x.strip() for x in os.getenv("QQ_ADMIN_LIST", "").split(",") if x.strip()])
    QQ_GROUP_KEYWORDS: list = field(default_factory=lambda: [x.strip() for x in os.getenv("QQ_GROUP_KEYWORDS", "").split(",") if x.strip()])
    QQ_GROUP_WHITELIST: list = field(default_factory=lambda: [x.strip() for x in os.getenv("QQ_GROUP_WHITELIST", "").split(",") if x.strip()])
    QQ_GROUP_BLACKLIST: list = field(default_factory=lambda: [x.strip() for x in os.getenv("QQ_GROUP_BLACKLIST", "").split(",") if x.strip()])
    QQ_PRIVATE_AUTO_REPLY: bool = field(default_factory=lambda: os.getenv("QQ_PRIVATE_AUTO_REPLY", "true").lower() == "true")
    
    # Bilibili
    BILIBILI_ENABLED: bool = field(default_factory=lambda: os.getenv("BILIBILI_ENABLED", "false").lower() == "true")
    BILIBILI_SESSDATA: str = field(default_factory=lambda: os.getenv("BILIBILI_SESSDATA", ""))
    BILIBILI_BILI_JCT: str = field(default_factory=lambda: os.getenv("BILIBILI_BILI_JCT", ""))
    BILIBILI_BUVID3: str = field(default_factory=lambda: os.getenv("BILIBILI_BUVID3", ""))
    
    # 频控配置
    FREQUENCY_LIMIT_SECONDS: int = field(default_factory=lambda: int(os.getenv("FREQUENCY_LIMIT_SECONDS", "3")))  # 每条消息最小间隔
    MAX_REPLY_PER_MINUTE: int = field(default_factory=lambda: int(os.getenv("MAX_REPLY_PER_MINUTE", "15")))  # 每分钟最大回复数
    
    # ========== 多模态配置 ==========
    # 语音识别 (sherpa-onnx)
    ASR_MODEL_PATH: str = field(default_factory=lambda: os.getenv("ASR_MODEL_PATH", str(BASE_DIR / "models" / "sherpa-onnx")))
    ASR_ENABLED: bool = field(default_factory=lambda: os.getenv("ASR_ENABLED", "false").lower() == "true")
    
    # 语音合成 (Edge-TTS)
    TTS_VOICE: str = field(default_factory=lambda: os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural"))
    TTS_RATE: str = field(default_factory=lambda: os.getenv("TTS_RATE", "+0%"))
    TTS_VOLUME: str = field(default_factory=lambda: os.getenv("TTS_VOLUME", "+0%"))
    TTS_ENABLED: bool = field(default_factory=lambda: os.getenv("TTS_ENABLED", "true").lower() == "true")
    
    # 表情包系统
    EMOTICON_PATH: str = field(default_factory=lambda: os.getenv("EMOTICON_PATH", str(BASE_DIR / "bigfatfish" / "visual" / "assets" / "emoticon_packs")))
    
    # 文生图 (可选)
    IMAGE_GEN_ENABLED: bool = field(default_factory=lambda: os.getenv("IMAGE_GEN_ENABLED", "false").lower() == "true")
    IMAGE_GEN_API_URL: str = field(default_factory=lambda: os.getenv("IMAGE_GEN_API_URL", ""))
    
    # ========== 视觉配置 ==========
    # Live2D
    LIVE2D_MODEL_PATH: str = field(default_factory=lambda: os.getenv("LIVE2D_MODEL_PATH", str(BASE_DIR / "bigfatfish" / "visual" / "assets" / "live2d_models")))
    
    # Web UI
    WEB_UI_HOST: str = field(default_factory=lambda: os.getenv("WEB_UI_HOST", "0.0.0.0"))
    WEB_UI_PORT: int = field(default_factory=lambda: int(os.getenv("WEB_UI_PORT", "8080")))
    
    # ========== 主动交互配置 ==========
    ACTIVE_INTERACTION_ENABLED: bool = field(default_factory=lambda: os.getenv("ACTIVE_INTERACTION_ENABLED", "true").lower() == "true")
    ACTIVE_INTERVAL_HOURS: int = field(default_factory=lambda: int(os.getenv("ACTIVE_INTERVAL_HOURS", "6")))  # 超过 N 小时未互动则主动发起
    
    # ========== 日志配置 ==========
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_PATH: str = field(default_factory=lambda: os.getenv("LOG_PATH", str(BASE_DIR / "bigfatfish" / "logs")))
    
    # ========== 人设配置 ==========
    PERSONA_NAME: str = field(default_factory=lambda: os.getenv("PERSONA_NAME", "大肥鱼"))
    PERSONA_GENDER: str = field(default_factory=lambda: os.getenv("PERSONA_GENDER", "女"))
    PERSONA_AGE: str = field(default_factory=lambda: os.getenv("PERSONA_AGE", "18"))
    
    # 鲸鱼娘人格开关（QQ机器人专用）
    USE_WHALE_PERSONA: bool = field(default_factory=lambda: os.getenv("USE_WHALE_PERSONA", "true").lower() == "true")
    
    def __post_init__(self):
        """初始化后检查必需配置"""
        # 检查 DeepSeek API Key（此处不抛异常，避免 APK 壳 / Web UI 启动即崩溃）
        if not self.DEEPSEEK_API_KEY or self.DEEPSEEK_API_KEY.startswith("your_"):
            import logging
            logging.getLogger(__name__).warning(
                "⚠ DEEPSEEK_API_KEY 未配置，AI 对话不可用；请在 .env 中配置"
            )
        
        # 创建必要目录
        Path(self.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.LOG_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.EMOTICON_PATH).mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
