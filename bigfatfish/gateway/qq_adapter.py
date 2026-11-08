# -*- coding: utf-8 -*-
"""
QQ 平台适配器
基于 NapCatQQ / Lagrange (OneBot v11 标准) 实现 QQ 群聊 + 私聊接入
支持 WebSocket 反向连接
"""
import json
import logging
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime

try:
    import websockets
except ImportError:
    websockets = None

from .router import MessageRouter, UnifiedMessage, UnifiedReply, Platform
from .frequency_control import FrequencyController
from ..config import settings

logger = logging.getLogger(__name__)


class QQAdapter:
    """
    QQ 平台适配器
    通过 OneBot v11 协议与 NapCatQQ/Lagrange 通信
    
    部署说明：
    1. 在手机上安装 NapCatQQ 或在 PC 运行 Lagrange
    2. 配置反向 WebSocket 连接到本程序
    3. 在 .env 中设置 QQ_WEBSOCKET_URL
    """
    
    def __init__(self, router: MessageRouter):
        """
        初始化 QQ 适配器
        
        Args:
            router: 消息路由器
        """
        self.router = router
        self.ws_url = settings.QQ_WEBSOCKET_URL
        self.http_url = settings.QQ_HTTP_URL
        self.bot_qq = settings.QQ_BOT_QQ
        self.frequency_ctrl = FrequencyController()
        self.websocket = None
        self._running = False
        
        # 注册到路由器
        self.router.register_platform("qq", self)
        
        logger.info(f"✓ QQ 适配器初始化 (WebSocket: {self.ws_url})")
    
    async def start(self):
        """启动 QQ WebSocket 监听"""
        if not websockets:
            logger.error("❌ websockets 未安装，无法启动 QQ 适配器")
            return
        
        self._running = True
        # 反向 WS（默认）：NapCat/Lagrange 主动连过来，本程序作为服务端
        if getattr(settings, "QQ_WS_MODE", "reverse") == "reverse":
            await self._start_reverse_server()
        else:
            await self._start_forward_client()
        logger.info("✓ QQ 适配器已停止")

    async def _start_reverse_server(self):
        """反向 WS 模式：本程序监听端口，等待 NapCat/Lagrange 连接"""
        from urllib.parse import urlparse
        u = urlparse(self.ws_url)
        host = u.hostname or "0.0.0.0"
        port = u.port or 3001
        logger.info(f"🚀 QQ 反向 WS 已监听 ws://{host}:{port}（等待 NapCat/Lagrange 连接）")

        async with websockets.serve(
            self._on_client_connected, host, port,
            ping_interval=30, ping_timeout=10
        ):
            while self._running:
                await asyncio.sleep(1)

    async def _on_client_connected(self, websocket, *args):
        """处理 NapCat/Lagrange 的反向连接"""
        if self.websocket and self.websocket is not websocket:
            logger.warning("⚠ 检测到新的 QQ 连接，旧连接将被替换")
        self.websocket = websocket
        logger.info("✓ NapCat/Lagrange 已连接")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._on_message(data)
                except Exception as e:
                    logger.error(f"❌ 处理消息失败: {e}")
        except Exception as e:
            logger.warning(f"⚠ QQ 连接断开: {e}")
        finally:
            if self.websocket is websocket:
                self.websocket = None

    async def _start_forward_client(self):
        """正向 WS 模式：本程序主动连接 NapCat/Lagrange 的 WS 服务器"""
        logger.info(f"🚀 正在连接 QQ 正向 WebSocket: {self.ws_url}")
        
        while self._running:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    logger.info(f"✓ QQ WebSocket 连接成功")
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._on_message(data)
                        except Exception as e:
                            logger.error(f"❌ 处理消息失败: {e}")
            
            except Exception as e:
                logger.warning(f"⚠ QQ WebSocket 断开 ({e})，5 秒后重连...")
                self.websocket = None
                await asyncio.sleep(5)
        
        logger.info("✓ QQ 适配器已停止")
    
    async def stop(self):
        """停止 QQ 适配器"""
        self._running = False
        if self.websocket:
            await self.websocket.close()
    
    async def _on_message(self, data: Dict):
        """
        处理 OneBot v11 消息事件
        
        Args:
            data: 原始事件数据
        """
        post_type = data.get("post_type")
        
        if post_type != "message":
            return
        
        message_type = data.get("message_type")
        
        # ========== 处理私聊消息 ==========
        if message_type == "private":
            await self._handle_private_message(data)
        
        # ========== 处理群聊消息（需要 @Bot 或触发词） ==========
        elif message_type == "group":
            await self._handle_group_message(data)
    
    async def _handle_private_message(self, data: Dict):
        """处理 QQ 私聊消息"""
        if not settings.QQ_PRIVATE_AUTO_REPLY:
            return

        user_id = str(data.get("user_id"))
        raw_message = data.get("raw_message", "") or self._extract_text(data.get("message", []))
        
        if not raw_message:
            return
        
        # 频率控制
        if not await self.frequency_ctrl.check(user_id):
            logger.debug(f"⚡ 用户 {user_id} 触发频率限制，跳过")
            return
        
        # 处理语音消息
        if self._has_voice(data.get("message", [])):
            raw_message = await self._handle_voice_message(data)
            if not raw_message:
                return
        
        unified_msg = UnifiedMessage(
            platform=Platform.QQ_PRIVATE,
            user_id=f"qq_{user_id}",
            raw_user_id=user_id,
            content=raw_message,
            message_type="text",
            raw_data=data
        )
        
        # 异步处理（不阻塞）
        asyncio.create_task(self.router.handle_message(unified_msg))
    
    async def _handle_group_message(self, data: Dict):
        """处理 QQ 群聊消息（需要 @Bot）"""
        group_id = str(data.get("group_id"))
        user_id = str(data.get("user_id"))
        message = data.get("message", [])
        
        # 检查是否 @了 Bot
        is_at_bot = any(
            seg.get("type") == "at" and str(seg.get("data", {}).get("qq")) == self.bot_qq
            for seg in message
        )
        
        # 群白名单 / 黑名单
        if settings.QQ_GROUP_WHITELIST and group_id not in settings.QQ_GROUP_WHITELIST:
            return
        if settings.QQ_GROUP_BLACKLIST and group_id in settings.QQ_GROUP_BLACKLIST:
            return

        # 关键词触发：不 @ 机器人也能响应
        full_text = self._extract_text(message)
        keyword_hit = any(kw and kw in full_text for kw in settings.QQ_GROUP_KEYWORDS)

        if not is_at_bot and not keyword_hit:
            return
        
        # 提取文本，去掉 @部分
        raw_message = self._extract_text_without_at(message)
        
        if not raw_message:
            return
        
        # 频率控制
        group_key = f"{group_id}_{user_id}"
        if not await self.frequency_ctrl.check(group_key):
            logger.debug(f"⚡ 群 {group_id} 触发频率限制")
            return
        
        unified_msg = UnifiedMessage(
            platform=Platform.QQ_GROUP,
            user_id=f"qq_{user_id}",  # 以用户 ID 为单位记忆，不以群区分
            raw_user_id=user_id,
            content=raw_message,
            message_type="text",
            raw_data={**data, "_group_id": group_id}
        )
        
        asyncio.create_task(self.router.handle_message(unified_msg))
    
    def _extract_text(self, message: list) -> str:
        """从消息段中提取纯文本"""
        return "".join(
            seg.get("data", {}).get("text", "")
            for seg in message
            if seg.get("type") == "text"
        ).strip()
    
    def _extract_text_without_at(self, message: list) -> str:
        """提取文本，忽略 @段"""
        return "".join(
            seg.get("data", {}).get("text", "")
            for seg in message
            if seg.get("type") == "text"
        ).strip()
    
    def _has_voice(self, message: list) -> bool:
        """检查消息中是否包含语音"""
        return any(seg.get("type") in ("record", "voice") for seg in message)
    
    async def _handle_voice_message(self, data: Dict) -> Optional[str]:
        """
        处理语音消息（ASR 转文字）
        
        Returns:
            识别出的文字，失败返回 None
        """
        try:
            from ..multimodal.asr_engine import ASREngine
            
            # 获取语音文件 URL
            message = data.get("message", [])
            voice_url = next(
                (seg.get("data", {}).get("url", "")
                 for seg in message
                 if seg.get("type") in ("record", "voice")),
                None
            )
            
            if not voice_url:
                return None
            
            # 调用 ASR
            asr = ASREngine()
            text = await asr.recognize_from_url(voice_url)
            
            logger.info(f"✓ 语音识别结果: {text}")
            return text
        
        except Exception as e:
            logger.error(f"❌ 语音识别失败: {e}")
            return None
    
    async def send_reply(self, reply: UnifiedReply):
        """
        发送回复到 QQ
        
        Args:
            reply: 统一回复对象
        """
        original = reply.original_message
        raw_data = original.raw_data
        
        platform = original.platform
        
        if platform == Platform.QQ_PRIVATE:
            user_id = original.raw_user_id
            
            # 发送文本
            if reply.text:
                await self._send_private_msg(user_id, reply.text)
            
            # 发送语音
            if reply.voice_path:
                await self._send_private_voice(user_id, reply.voice_path)
            
            # 发送表情包
            if reply.image_path:
                await self._send_private_image(user_id, reply.image_path)
        
        elif platform == Platform.QQ_GROUP:
            group_id = raw_data.get("_group_id")
            user_id = original.raw_user_id
            
            # 发送文本（附带 @用户）
            if reply.text:
                at_user = f"[CQ:at,qq={user_id}] "
                await self._send_group_msg(group_id, at_user + reply.text)
            
            # 发送表情包
            if reply.image_path:
                await self._send_group_image(group_id, reply.image_path)
    
    async def _send_action(self, action: str, params: Dict):
        """发送 OneBot v11 API 动作"""
        if not self.websocket:
            logger.error("❌ WebSocket 未连接，无法发送消息")
            return
        
        payload = {
            "action": action,
            "params": params,
            "echo": str(time.time())
        }
        
        await self.websocket.send(json.dumps(payload, ensure_ascii=False))
    
    async def _send_private_msg(self, user_id: str, text: str):
        """发送私聊文本"""
        await self._send_action("send_private_msg", {
            "user_id": int(user_id),
            "message": text
        })
    
    async def _send_private_voice(self, user_id: str, voice_path: str):
        """发送私聊语音"""
        await self._send_action("send_private_msg", {
            "user_id": int(user_id),
            "message": f"[CQ:record,file=file:///{voice_path}]"
        })
    
    async def _send_private_image(self, user_id: str, image_path: str):
        """发送私聊图片"""
        await self._send_action("send_private_msg", {
            "user_id": int(user_id),
            "message": f"[CQ:image,file=file:///{image_path}]"
        })
    
    async def _send_group_msg(self, group_id: str, text: str):
        """发送群聊文本"""
        await self._send_action("send_group_msg", {
            "group_id": int(group_id),
            "message": text
        })
    
    async def _send_group_image(self, group_id: str, image_path: str):
        """发送群聊图片"""
        await self._send_action("send_group_msg", {
            "group_id": int(group_id),
            "message": f"[CQ:image,file=file:///{image_path}]"
        })
