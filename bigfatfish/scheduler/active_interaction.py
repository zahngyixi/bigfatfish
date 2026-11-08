# -*- coding: utf-8 -*-
"""
主动交互引擎
基于定时任务，检测用户离线时长，主动发起关心对话
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Callable
from datetime import datetime

from ..config import settings, PromptTemplates

logger = logging.getLogger(__name__)


class ActiveInteractionEngine:
    """主动交互引擎（缺你 Cron）"""
    
    def __init__(self, router=None, agent=None):
        """
        初始化主动交互引擎
        
        Args:
            router: 消息路由器（用于发送消息）
            agent: AI Agent
        """
        self.router = router
        self.agent = agent
        
        # 记录每个用户的最后互动时间 (user_id -> timestamp)
        self._last_active: Dict[str, float] = {}
        # 记录上次主动发起时间，避免短时间重复打扰
        self._last_proactive: Dict[str, float] = {}
        
        self._running = False
        self._interval_hours = settings.ACTIVE_INTERVAL_HOURS
        
        # 检查间隔（每 30 分钟检查一次是否有用户需要主动问候）
        self._check_interval_seconds = 30 * 60
    
    def update_user_activity(self, user_id: str):
        """
        更新用户活跃时间（在收到消息时调用）
        
        Args:
            user_id: 用户 ID
        """
        self._last_active[user_id] = time.time()
    
    async def start(self):
        """启动主动交互引擎"""
        if not settings.ACTIVE_INTERACTION_ENABLED:
            logger.info("ℹ 主动交互功能已禁用，跳过")
            return
        
        self._running = True
        logger.info(f"✓ 主动交互引擎启动 (每 {self._interval_hours} 小时检查一次用户)")
        
        while self._running:
            await asyncio.sleep(self._check_interval_seconds)
            await self._check_and_greet()
    
    async def stop(self):
        """停止主动交互引擎"""
        self._running = False
    
    async def _check_and_greet(self):
        """检查是否有需要主动问候的用户"""
        if not self.agent:
            return
        
        now = time.time()
        threshold = self._interval_hours * 3600
        
        for user_id, last_time in list(self._last_active.items()):
            # 检查是否超过阈值时间未互动
            if now - last_time < threshold:
                continue
            
            # 检查上次主动问候的时间（避免重复）
            last_proactive = self._last_proactive.get(user_id, 0)
            if now - last_proactive < threshold:
                continue
            
            # 触发主动问候
            await self._greet_user(user_id, now - last_time)
    
    async def _greet_user(self, user_id: str, inactive_seconds: float):
        """
        主动向用户发送问候消息
        
        Args:
            user_id: 用户 ID
            inactive_seconds: 用户离线时长（秒）
        """
        try:
            inactive_hours = int(inactive_seconds / 3600)
            logger.info(f"💬 主动问候用户 {user_id} (已离线 {inactive_hours} 小时)")
            
            # 检索用户的记忆
            recent_memory = ""
            if self.agent.memory_manager:
                recent_memory = await self.agent.memory_manager.retrieve_relevant_memory(
                    "用户最近的状态和心情",
                    user_id,
                    top_k=3
                )
            
            # 构建主动问候 Prompt
            proactive_prompt = PromptTemplates.ACTIVE_CONVERSATION_PROMPT.format(
                hours=inactive_hours,
                recent_memory=recent_memory if recent_memory else "暂无记忆"
            )
            
            # 生成问候语
            greeting = await self.agent.chat(
                proactive_prompt,
                user_id=user_id,
                platform="proactive",
                system_prompt=PromptTemplates.SYSTEM_PERSONA
            )
            
            if not greeting:
                return
            
            # 解析情绪
            from ..gateway.router import MessageRouter
            clean_text, emotion = self.router._parse_emotion_tag(greeting) if self.router else (greeting, None)
            
            # 通过路由器发送消息
            if self.router:
                await self._send_proactive_message(user_id, clean_text, emotion)
            
            # 记录本次主动问候时间
            self._last_proactive[user_id] = time.time()
            
            logger.info(f"✓ 问候消息已发送给用户 {user_id}: {clean_text[:30]}...")
        
        except Exception as e:
            logger.error(f"❌ 主动问候失败: {e}")
    
    async def _send_proactive_message(self, user_id: str, text: str, emotion: Optional[str]):
        """发送主动问候消息"""
        try:
            # 根据 user_id 前缀判断平台
            if user_id.startswith("qq_"):
                raw_uid = user_id[3:]
                platform_id = "qq"
                
                if platform_id in self.router.platforms:
                    adapter = self.router.platforms[platform_id]
                    await adapter._send_private_msg(raw_uid, text)
            
            elif user_id.startswith("bili_"):
                raw_uid = user_id[5:]
                platform_id = "bilibili"
                
                if platform_id in self.router.platforms:
                    adapter = self.router.platforms[platform_id]
                    # Bilibili 主动消息
                    from ..gateway.router import UnifiedReply, UnifiedMessage, Platform
                    
                    dummy_msg = UnifiedMessage(
                        platform=Platform.BILIBILI_MSG,
                        user_id=user_id,
                        raw_user_id=raw_uid,
                        content="",
                        message_type="text",
                        raw_data={}
                    )
                    
                    reply = UnifiedReply(
                        original_message=dummy_msg,
                        text=text,
                        emotion=emotion
                    )
                    
                    await adapter.send_reply(reply)
        
        except Exception as e:
            logger.error(f"❌ 发送主动消息失败: {e}")
