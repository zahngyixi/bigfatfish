# -*- coding: utf-8 -*-
"""
消息路由器
统一接收各平台消息，调用 AI 处理，并将回复路由回原平台
"""
import asyncio
import logging
from typing import Dict, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """平台枚举"""
    QQ_PRIVATE = "qq_private"
    QQ_GROUP = "qq_group"
    BILIBILI_MSG = "bilibili_msg"
    BILIBILI_COMMENT = "bilibili_comment"
    WEB = "web"


@dataclass
class UnifiedMessage:
    """统一消息格式"""
    platform: Platform
    user_id: str                  # 用户唯一标识（跨平台）
    raw_user_id: str              # 平台原始用户 ID
    content: str                  # 消息文本内容
    message_type: str             # 消息类型 (text/voice/image)
    raw_data: Dict                # 原始消息数据（用于回复路由）
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class UnifiedReply:
    """统一回复格式"""
    original_message: UnifiedMessage
    text: str                         # 回复文本
    emotion: Optional[str] = None     # 情绪标签
    voice_path: Optional[str] = None  # 语音文件路径
    image_path: Optional[str] = None  # 图片路径（表情包/生成图）


class MessageRouter:
    """
    消息路由器
    将不同平台的消息统一处理后分发给 AI，并将回复路由回原平台
    """
    
    def __init__(self):
        """初始化路由器"""
        self.platforms = {}       # 注册的平台适配器
        self.agent = None         # AI Agent
        self.emotion_system = None
        self.tts_engine = None
        
        logger.info("✓ 消息路由器初始化成功")
    
    def register_platform(self, platform_id: str, adapter):
        """
        注册平台适配器
        
        Args:
            platform_id: 平台 ID
            adapter: 平台适配器实例
        """
        self.platforms[platform_id] = adapter
        logger.info(f"✓ 平台适配器已注册: {platform_id}")
    
    def set_agent(self, agent):
        """设置 AI Agent"""
        self.agent = agent
    
    def set_emotion_system(self, emotion_system):
        """设置情绪系统"""
        self.emotion_system = emotion_system
    
    def set_tts_engine(self, tts_engine):
        """设置 TTS 引擎"""
        self.tts_engine = tts_engine
    
    async def handle_message(self, unified_msg: UnifiedMessage):
        """
        处理统一消息（核心路由逻辑）
        
        Args:
            unified_msg: 统一消息对象
        """
        logger.info(f"📩 [{unified_msg.platform}] 用户 {unified_msg.user_id}: {unified_msg.content[:50]}...")
        
        try:
            # ========== 1. AI 处理（流式） ==========
            if not self.agent:
                logger.error("❌ AI Agent 未初始化")
                return
            
            full_response = ""
            async for chunk in self.agent.chat_stream(
                user_message=unified_msg.content,
                user_id=unified_msg.user_id,
                platform=unified_msg.platform.value
            ):
                full_response += chunk
            
            if not full_response:
                logger.warning("⚠ AI 返回空回复")
                return
            
            # ========== 2. 解析情绪标签 ==========
            clean_text, emotion = self._parse_emotion_tag(full_response)
            
            # ========== 3. 构建回复对象 ==========
            reply = UnifiedReply(
                original_message=unified_msg,
                text=clean_text,
                emotion=emotion
            )
            
            # ========== 4. 可选：生成表情包 ==========
            if self.emotion_system and emotion:
                emoticon_path = await self.emotion_system.get_emoticon(emotion)
                if emoticon_path:
                    reply.image_path = emoticon_path
            
            # ========== 5. 可选：生成语音 ==========
            if self.tts_engine and settings.TTS_ENABLED:
                voice_path = await self.tts_engine.synthesize(clean_text)
                if voice_path:
                    reply.voice_path = voice_path
            
            # ========== 6. 回复到原平台 ==========
            await self._route_reply(reply)
            
            # ========== 7. 保存助手回复到短期记忆 ==========
            if self.agent.memory_manager:
                await self.agent.memory_manager.add_to_short_memory(
                    unified_msg.user_id,
                    {"role": "assistant", "content": clean_text}
                )
        
        except Exception as e:
            logger.error(f"❌ 消息处理失败: {e}", exc_info=True)
    
    def _parse_emotion_tag(self, text: str) -> tuple:
        """
        从回复文本中解析情绪标签
        
        Args:
            text: 包含 [emotion: xxx] 标签的文本
            
        Returns:
            (clean_text, emotion_label)
        """
        import re
        
        emotion = None
        clean_text = text
        
        # 匹配 [emotion: happy] 格式
        pattern = r'\[emotion:\s*(\w+)\]'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            emotion = match.group(1).lower()
            clean_text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
        
        return clean_text, emotion
    
    async def _route_reply(self, reply: UnifiedReply):
        """
        将回复路由回原始平台
        
        Args:
            reply: 统一回复对象
        """
        original = reply.original_message
        platform_id = original.platform.value.split('_')[0]  # 提取平台名 (qq/bilibili/web)
        
        if platform_id not in self.platforms:
            logger.warning(f"⚠ 未找到平台适配器: {platform_id}")
            return
        
        adapter = self.platforms[platform_id]
        
        try:
            await adapter.send_reply(reply)
        except Exception as e:
            logger.error(f"❌ 回复发送失败 ({platform_id}): {e}")
