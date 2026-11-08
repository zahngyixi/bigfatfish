# -*- coding: utf-8 -*-
"""
语音合成引擎 (TTS)
主方案: edge-tts (无需本地模型, 纯 Python, ARM64 完全兼容)
备用方案: pyttsx3 (本地 TTS)

ARM64 Termux 兼容性说明:
─────────────────────────────────────────────────────────────────
✅ 主推: edge-tts
   pip install edge-tts
   调用微软在线 TTS，纯 Python HTTP 实现，无 C 扩展，ARM64 完美兼容
   声线: zh-CN-XiaoxiaoNeural (小晓，温柔女声)
         zh-CN-XiaoYiNeural  (小依，活泼女声)
         zh-CN-XiaochenNeural (晓辰，甜美女声)

✅ 备用: pyttsx3
   pip install pyttsx3
   在 Termux 上需要 espeak: pkg install espeak
─────────────────────────────────────────────────────────────────
"""
import logging
import asyncio
import os
import time
import tempfile
from pathlib import Path
from typing import Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

from ..config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    语音合成引擎
    主要使用 edge-tts (ARM64 完全兼容，无需本地模型)
    """
    
    # TTS 输出目录
    OUTPUT_DIR = Path(settings.LOG_PATH).parent / "tts_output"
    
    def __init__(self):
        """初始化 TTS 引擎"""
        self.engine_type = None
        self.voice = settings.TTS_VOICE
        self.rate = settings.TTS_RATE
        self.volume = settings.TTS_VOLUME
        
        # 创建输出目录
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        if settings.TTS_ENABLED:
            self._detect_engine()
    
    def _detect_engine(self):
        """检测可用 TTS 引擎"""
        if edge_tts:
            self.engine_type = "edge_tts"
            logger.info(f"✓ TTS 引擎: edge-tts (声线: {self.voice})")
        else:
            try:
                import pyttsx3
                self.engine_type = "pyttsx3"
                logger.info("✓ TTS 引擎: pyttsx3 (备用)")
            except ImportError:
                logger.warning("⚠ 无可用 TTS 引擎，语音合成功能禁用")
    
    async def synthesize(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        将文本合成为语音文件
        
        Args:
            text: 要合成的文本
            output_path: 输出路径（可选，不指定则自动生成）
            
        Returns:
            生成的音频文件路径，失败返回 None
        """
        if not self.engine_type:
            logger.debug("⚠ TTS 引擎未初始化")
            return None
        
        if not text or not text.strip():
            return None
        
        # 截断过长文本（TTS 不需要发送全文）
        if len(text) > 200:
            text = text[:200] + "……"
        
        # 生成输出路径
        if not output_path:
            ts = int(time.time() * 1000)
            output_path = str(self.OUTPUT_DIR / f"tts_{ts}.mp3")
        
        try:
            if self.engine_type == "edge_tts":
                return await self._synthesize_edge_tts(text, output_path)
            elif self.engine_type == "pyttsx3":
                return await self._synthesize_pyttsx3(text, output_path)
        
        except Exception as e:
            logger.error(f"❌ TTS 合成失败: {e}")
            return None
    
    async def _synthesize_edge_tts(self, text: str, output_path: str) -> Optional[str]:
        """
        使用 edge-tts 合成（在线，ARM64 完美兼容）
        
        edge-tts 调用微软 Bing TTS 在线服务，无需本地模型
        网络要求：访问 api.microsofttranslator.com
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
            )
            
            await communicate.save(output_path)
            
            logger.debug(f"✓ TTS 合成成功: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"❌ edge-tts 合成失败: {e}")
            return None
    
    async def _synthesize_pyttsx3(self, text: str, output_path: str) -> Optional[str]:
        """使用 pyttsx3 合成（本地，备用方案）"""
        try:
            import pyttsx3
            
            def _synth():
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                
                # 尝试选择中文声音
                for voice in voices:
                    if "chinese" in voice.id.lower() or "zh" in voice.id.lower():
                        engine.setProperty("voice", voice.id)
                        break
                
                engine.setProperty("rate", 150)
                engine.save_to_file(text, output_path)
                engine.runAndWait()
            
            await asyncio.get_event_loop().run_in_executor(None, _synth)
            
            if Path(output_path).exists():
                return output_path
            return None
        
        except Exception as e:
            logger.error(f"❌ pyttsx3 合成失败: {e}")
            return None
    
    async def list_voices(self) -> list:
        """列出所有可用的 edge-tts 中文声线"""
        if not edge_tts:
            return []
        
        try:
            voices = await edge_tts.list_voices()
            cn_voices = [
                {
                    "name": v["ShortName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"],
                    "friendly_name": v.get("FriendlyName", "")
                }
                for v in voices
                if v.get("Locale", "").startswith("zh-")
            ]
            return cn_voices
        
        except Exception as e:
            logger.error(f"❌ 获取声线列表失败: {e}")
            return []
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """清理旧的 TTS 文件"""
        try:
            now = time.time()
            count = 0
            
            for f in self.OUTPUT_DIR.glob("tts_*.mp3"):
                if now - f.stat().st_mtime > max_age_hours * 3600:
                    f.unlink()
                    count += 1
            
            if count:
                logger.info(f"✓ 清理了 {count} 个过期 TTS 文件")
        
        except Exception as e:
            logger.debug(f"TTS 文件清理异常: {e}")
