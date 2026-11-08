# -*- coding: utf-8 -*-
"""
Web UI 服务器
基于 aiohttp 提供 Live2D 前端页面服务
支持手机端访问（扫码即用）
"""
import logging
import asyncio
import json
from pathlib import Path
from typing import Optional

try:
    from aiohttp import web
    import aiohttp
except ImportError:
    web = None
    aiohttp = None

from ..config import settings

logger = logging.getLogger(__name__)

# 静态资源目录
WEB_ROOT = Path(__file__).parent / "assets" / "web"
LIVE2D_ROOT = Path(__file__).parent / "assets" / "live2d_models"
TTS_ROOT = Path(settings.LOG_PATH).parent / "tts_output"


class UIServer:
    """Web UI 服务器"""
    
    def __init__(self, router=None):
        """
        初始化 Web UI 服务器
        
        Args:
            router: 消息路由器（用于 WebSocket 连接）
        """
        self.router = router
        self.app = None
        self.runner = None
        self._ws_clients = set()
        
        if web:
            self._setup_app()
    
    def _setup_app(self):
        """配置 aiohttp 应用"""

        # CORS：允许 APK 壳（file:// / 局域网）与云端 PWA 跨域访问后端
        @web.middleware
        async def cors_middleware(request, handler):
            if request.headers.get("Upgrade", "").lower() == "websocket":
                return await handler(request)
            if request.method == "OPTIONS":
                resp = web.Response(status=204)
            else:
                resp = await handler(request)
            resp.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return resp

        self.app = web.Application(middlewares=[cors_middleware])

        # add_static 要求目录已存在
        TTS_ROOT.mkdir(parents=True, exist_ok=True)
        LIVE2D_ROOT.mkdir(parents=True, exist_ok=True)

        # 路由
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/sw.js", self.handle_sw)
        self.app.router.add_get("/ws", self.handle_websocket)
        self.app.router.add_post("/api/chat", self.handle_chat_api)
        self.app.router.add_post("/api/tts", self.handle_tts_api)
        self.app.router.add_static("/static", str(WEB_ROOT), name="static")
        self.app.router.add_static("/tts", str(TTS_ROOT), name="tts")
        self.app.router.add_static("/live2d", str(LIVE2D_ROOT), name="live2d")

    async def handle_sw(self, request) -> web.Response:
        """Service Worker 必须从根路径提供，才能控制 '/' 作用域"""
        p = WEB_ROOT / "sw.js"
        if not p.exists():
            return web.Response(status=404)
        return web.Response(
            text=p.read_text(encoding="utf-8"),
            content_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    async def handle_tts_api(self, request) -> web.Response:
        """文本转语音：返回 /tts/xxx.mp3 地址，供前端播放并做口型同步"""
        try:
            body = await request.json()
            text = (body.get("text") or "").strip()
            if not text:
                return web.json_response({"url": None, "reason": "empty_text"}, status=400)

            tts = getattr(self.router, "tts_engine", None) if self.router else None
            if not tts or not getattr(tts, "engine_type", None):
                return web.json_response({"url": None, "reason": "tts_disabled"})

            path = await tts.synthesize(text)
            if not path:
                return web.json_response({"url": None, "reason": "synthesize_failed"})

            return web.json_response({"url": f"/tts/{Path(path).name}"})
        except Exception as e:
            logger.error(f"❌ TTS 接口异常: {e}")
            return web.json_response({"url": None, "error": str(e)}, status=500)
    
    async def start(self):
        """启动 Web UI 服务器"""
        if not web:
            logger.error("❌ aiohttp 未安装，无法启动 Web UI")
            return
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, settings.WEB_UI_HOST, settings.WEB_UI_PORT)
        await site.start()
        
        # 生成二维码（方便手机扫码访问）
        self._print_qrcode()
        
        logger.info(f"✓ Web UI 已启动: http://{settings.WEB_UI_HOST}:{settings.WEB_UI_PORT}")
    
    async def stop(self):
        """停止服务器"""
        if self.runner:
            await self.runner.cleanup()
    
    def _print_qrcode(self):
        """在终端打印二维码"""
        try:
            import qrcode
            import socket
            
            # 获取本机 IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            url = f"http://{local_ip}:{settings.WEB_UI_PORT}"
            
            qr = qrcode.QRCode(border=1)
            qr.add_data(url)
            qr.make(fit=True)
            
            print("\n" + "="*50)
            print("📱 扫描二维码访问 AI 伴侣界面:")
            print(f"   {url}")
            print("="*50)
            qr.print_ascii(invert=True)
            print("="*50 + "\n")
        
        except Exception:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            finally:
                s.close()
            logger.info(f"📱 请在手机浏览器访问: http://{local_ip}:{settings.WEB_UI_PORT}")
    
    async def handle_index(self, request) -> web.Response:
        """处理主页请求"""
        index_file = WEB_ROOT / "index.html"
        if index_file.exists():
            return web.FileResponse(str(index_file))
        return web.Response(text="<h1>大肥鱼 AI 伴侣</h1><p>前端资源未找到，请检查 visual/assets/web/ 目录</p>", content_type="text/html")
    
    async def handle_websocket(self, request) -> web.WebSocketResponse:
        """处理 WebSocket 连接（前端与后端实时通信）"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self._ws_clients.add(ws)
        logger.info(f"✓ WebSocket 客户端连接 ({len(self._ws_clients)} 个连接)")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_ws_message(ws, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        
        finally:
            self._ws_clients.discard(ws)
        
        return ws
    
    async def _handle_ws_message(self, ws, data: str):
        """处理 WebSocket 消息"""
        try:
            payload = json.loads(data)
            msg_type = payload.get("type")
            
            if msg_type == "chat":
                # 用户发送的聊天消息
                text = payload.get("text", "")
                user_id = payload.get("user_id", "web_user")
                
                if not text or not self.router:
                    return
                
                from ..gateway.router import UnifiedMessage, Platform
                
                unified_msg = UnifiedMessage(
                    platform=Platform.WEB,
                    user_id=f"web_{user_id}",
                    raw_user_id=user_id,
                    content=text,
                    message_type="text",
                    raw_data={"ws": ws}
                )
                
                # 流式返回到前端
                await self._handle_web_message_stream(ws, unified_msg)
        
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"❌ WebSocket 消息处理失败: {e}")
    
    async def _handle_web_message_stream(self, ws, unified_msg):
        """流式处理 Web 端消息并推送给前端"""
        if not self.router or not self.router.agent:
            return
        
        full_text = ""
        
        # 通知前端开始流式回复
        await ws.send_json({"type": "stream_start"})
        
        async for chunk in self.router.agent.chat_stream(
            unified_msg.content,
            unified_msg.user_id,
            "web"
        ):
            full_text += chunk
            # 逐块推送到前端
            await ws.send_json({"type": "stream_chunk", "text": chunk})
        
        # 解析情绪
        from ..gateway.router import MessageRouter
        clean_text, emotion = self.router._parse_emotion_tag(full_text)
        
        # 发送完成信号
        await ws.send_json({
            "type": "stream_end",
            "full_text": clean_text,
            "emotion": emotion or "neutral"
        })
    
    async def handle_chat_api(self, request) -> web.Response:
        """HTTP API 接口（非流式，兼容旧客户端）"""
        try:
            body = await request.json()
            text = body.get("text", "")
            user_id = body.get("user_id", "api_user")
            
            if not text or not self.router or not self.router.agent:
                return web.json_response({"error": "invalid request"}, status=400)
            
            reply = await self.router.agent.chat(text, f"web_{user_id}", "web")
            
            from ..gateway.router import MessageRouter
            clean_text, emotion = self.router._parse_emotion_tag(reply)
            
            return web.json_response({
                "text": clean_text,
                "emotion": emotion or "neutral"
            })
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def broadcast_emotion(self, emotion: str):
        """广播情绪变化给所有 WebSocket 客户端（驱动 Live2D）"""
        if not self._ws_clients:
            return
        
        msg = json.dumps({"type": "emotion", "emotion": emotion})
        await asyncio.gather(
            *[ws.send_str(msg) for ws in self._ws_clients if not ws.closed],
            return_exceptions=True
        )
