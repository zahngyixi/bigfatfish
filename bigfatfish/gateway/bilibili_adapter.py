# -*- coding: utf-8 -*-
"""
Bilibili 平台适配器
支持监听 B 站私信和动态评论区
"""
import logging
import asyncio
from typing import Optional

try:
    from bilibili_api import user, settings as bili_settings
    from bilibili_api.user import User
    from bilibili_api import Credential
except ImportError:
    User = None
    Credential = None

from .router import MessageRouter, UnifiedMessage, UnifiedReply, Platform
from .frequency_control import FrequencyController
from ..config import settings

logger = logging.getLogger(__name__)


class BilibiliAdapter:
    """
    B 站平台适配器
    使用 bilibili-api-python 监听私信消息
    """
    
    def __init__(self, router: MessageRouter):
        """初始化 B 站适配器"""
        self.router = router
        self.frequency_ctrl = FrequencyController()
        self.credential = None
        self._running = False
        self._last_msg_seqno = 0
        
        # 注册到路由器
        self.router.register_platform("bilibili", self)
        
        logger.info("✓ Bilibili 适配器初始化")
    
    def _init_credential(self):
        """初始化 B 站凭证"""
        if not Credential:
            logger.error("❌ bilibili_api 未安装")
            return False
        
        if not all([settings.BILIBILI_SESSDATA, settings.BILIBILI_BILI_JCT, settings.BILIBILI_BUVID3]):
            logger.error("❌ Bilibili 凭证未完整配置")
            return False
        
        self.credential = Credential(
            sessdata=settings.BILIBILI_SESSDATA,
            bili_jct=settings.BILIBILI_BILI_JCT,
            buvid3=settings.BILIBILI_BUVID3,
        )
        return True
    
    async def start(self):
        """启动 B 站消息监听"""
        if not settings.BILIBILI_ENABLED:
            logger.info("ℹ Bilibili 接入已禁用，跳过")
            return
        
        if not self._init_credential():
            return
        
        self._running = True
        logger.info("🚀 开始监听 B 站消息...")
        
        while self._running:
            try:
                await self._poll_messages()
                await asyncio.sleep(15)  # 每 15 秒轮询一次（避免频率过高）
            except Exception as e:
                logger.error(f"❌ B 站消息轮询出错: {e}")
                await asyncio.sleep(30)
    
    async def _poll_messages(self):
        """轮询 B 站私信"""
        try:
            from bilibili_api.session import Session
            
            session = Session(credential=self.credential)
            sessions_data = await session.get_sessions()
            
            if not sessions_data:
                return
            
            for session_item in sessions_data.get("session_list", []):
                await self._process_session(session_item)
        
        except Exception as e:
            logger.debug(f"B 站轮询异常: {e}")
    
    async def _process_session(self, session_item: dict):
        """处理单条会话"""
        try:
            sender_uid = str(session_item.get("talker_id", ""))
            last_msg = session_item.get("last_msg", {})
            
            content_obj = last_msg.get("content", {})
            if isinstance(content_obj, str):
                import json
                try:
                    content_obj = json.loads(content_obj)
                except Exception:
                    pass
            
            # 只处理文字私信
            msg_type = last_msg.get("msg_type", 0)
            if msg_type != 1:
                return
            
            text = content_obj.get("content", "").strip() if isinstance(content_obj, dict) else str(content_obj)
            
            if not text:
                return
            
            # 用 seqno 去重
            seqno = last_msg.get("msg_seqno", 0)
            if seqno <= self._last_msg_seqno:
                return
            
            self._last_msg_seqno = max(self._last_msg_seqno, seqno)
            
            # 频率控制
            if not await self.frequency_ctrl.check(sender_uid):
                return
            
            unified_msg = UnifiedMessage(
                platform=Platform.BILIBILI_MSG,
                user_id=f"bili_{sender_uid}",
                raw_user_id=sender_uid,
                content=text,
                message_type="text",
                raw_data=session_item
            )
            
            asyncio.create_task(self.router.handle_message(unified_msg))
        
        except Exception as e:
            logger.debug(f"处理 B 站会话异常: {e}")
    
    async def send_reply(self, reply: UnifiedReply):
        """发送 B 站私信回复"""
        if not self.credential:
            logger.error("❌ B 站凭证未初始化")
            return
        
        original = reply.original_message
        uid = original.raw_user_id
        
        try:
            from bilibili_api.session import send_msg
            
            # 发送文本
            if reply.text:
                await send_msg(
                    self.credential,
                    int(uid),
                    msg_type=1,
                    content=reply.text
                )
                logger.info(f"✓ B 站回复已发送给 {uid}")
        
        except Exception as e:
            logger.error(f"❌ B 站发送消息失败: {e}")
