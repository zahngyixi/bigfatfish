# -*- coding: utf-8 -*-
"""
语音识别引擎 (ASR)
主方案: sherpa-onnx (支持 ARM64 aarch64，有官方预编译 wheel)
备用方案: whisper.cpp Python bindings
"""
import logging
import asyncio
from pathlib import Path
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


class ASREngine:
    """
    语音识别引擎
    
    ARM64 Termux 兼容性说明:
    ─────────────────────────────────────────────────────────────────
    ✅ 推荐: sherpa-onnx
       pip install sherpa-onnx
       官方提供 aarch64 Linux wheel，Termux 可直接安装
       模型下载: https://github.com/k2-fsa/sherpa-onnx/releases
       推荐中文模型: sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
    
    ✅ 备用: faster-whisper (CTranslate2 后端)
       pip install faster-whisper
       CTranslate2 提供 aarch64 wheel，支持 Termux
       模型: tiny / base (适合手机内存)
    
    ❌ 不兼容: openai-whisper (依赖 torch，ARM64 安装复杂)
    ─────────────────────────────────────────────────────────────────
    """
    
    def __init__(self):
        """初始化 ASR 引擎"""
        self.engine = None
        self.engine_type = None
        
        if settings.ASR_ENABLED:
            self._init_engine()
    
    def _init_engine(self):
        """按优先级初始化 ASR 引擎"""
        # 优先尝试 sherpa-onnx
        if self._try_init_sherpa():
            return
        
        # 备用: faster-whisper
        if self._try_init_faster_whisper():
            return
        
        logger.error("❌ 没有可用的 ASR 引擎，请安装 sherpa-onnx 或 faster-whisper")
    
    def _try_init_sherpa(self) -> bool:
        """初始化 sherpa-onnx"""
        try:
            import sherpa_onnx
        except ImportError:
            return False
        
        model_path = Path(settings.ASR_MODEL_PATH)
        
        if not model_path.exists():
            logger.warning(f"⚠ sherpa-onnx 模型目录不存在: {model_path}")
            logger.warning("请运行 deploy.sh 下载模型，或手动下载:")
            logger.warning("  https://github.com/k2-fsa/sherpa-onnx/releases")
            return False
        
        try:
            # 查找必要的模型文件
            encoder = str(next(model_path.glob("*encoder*.onnx"), None) or "")
            decoder = str(next(model_path.glob("*decoder*.onnx"), None) or "")
            joiner = str(next(model_path.glob("*joiner*.onnx"), None) or "")
            tokens = str(next(model_path.glob("tokens.txt"), None) or "")
            
            if not all([encoder, decoder, joiner, tokens]):
                logger.warning("⚠ sherpa-onnx 模型文件不完整")
                return False
            
            # 初始化流式 ASR
            self.engine = sherpa_onnx.OnlineRecognizer.from_transducer(
                encoder=encoder,
                decoder=decoder,
                joiner=joiner,
                tokens=tokens,
                num_threads=2,  # 手机端限制线程数
                sample_rate=16000,
                feature_dim=80,
                enable_endpoint_detection=True,
                rule1_min_trailing_silence=2.4,
                rule2_min_trailing_silence=1.2,
                rule3_min_utterance_length=300,
            )
            
            self.engine_type = "sherpa_onnx"
            logger.info("✓ sherpa-onnx ASR 引擎初始化成功")
            return True
        
        except Exception as e:
            logger.warning(f"⚠ sherpa-onnx 初始化失败: {e}")
            return False
    
    def _try_init_faster_whisper(self) -> bool:
        """初始化 faster-whisper（ARM64 备用方案）"""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return False
        
        try:
            # 使用 tiny 模型（适合手机内存）
            self.engine = WhisperModel(
                "tiny",
                device="cpu",
                compute_type="int8",  # 量化，减少内存
                num_workers=1,
                download_root=str(Path(settings.ASR_MODEL_PATH) / "whisper")
            )
            self.engine_type = "faster_whisper"
            logger.info("✓ faster-whisper ASR 引擎初始化成功（备用方案）")
            return True
        
        except Exception as e:
            logger.warning(f"⚠ faster-whisper 初始化失败: {e}")
            return False
    
    async def recognize(self, audio_path: str) -> Optional[str]:
        """
        识别音频文件
        
        Args:
            audio_path: 音频文件路径 (.wav / .ogg / .mp3)
            
        Returns:
            识别出的文字，失败返回 None
        """
        if not self.engine:
            logger.warning("⚠ ASR 引擎未初始化")
            return None
        
        if not Path(audio_path).exists():
            logger.error(f"❌ 音频文件不存在: {audio_path}")
            return None
        
        try:
            # 在线程池中运行（避免阻塞异步循环）
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._recognize_sync,
                audio_path
            )
        except Exception as e:
            logger.error(f"❌ 语音识别失败: {e}")
            return None
    
    def _recognize_sync(self, audio_path: str) -> Optional[str]:
        """同步识别（在线程池中运行）"""
        try:
            # 先转换为 WAV（16kHz 单声道）
            wav_path = self._convert_to_wav(audio_path)
            
            if self.engine_type == "sherpa_onnx":
                return self._recognize_sherpa(wav_path)
            elif self.engine_type == "faster_whisper":
                return self._recognize_faster_whisper(wav_path)
        
        except Exception as e:
            logger.error(f"❌ 同步识别失败: {e}")
            return None
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """
        将音频转换为 16kHz 单声道 WAV
        使用 pydub（ffmpeg 后端，Termux 可安装 ffmpeg）
        """
        if audio_path.endswith(".wav"):
            return audio_path
        
        output_path = audio_path.rsplit(".", 1)[0] + "_converted.wav"
        
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_channels(1).set_frame_rate(16000)
            audio.export(output_path, format="wav")
            return output_path
        
        except Exception:
            logger.warning(f"⚠ pydub 转换失败，尝试直接使用 ffmpeg")
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_path,
                "-ar", "16000", "-ac", "1",
                output_path
            ], capture_output=True)
            return output_path if Path(output_path).exists() else audio_path
    
    def _recognize_sherpa(self, wav_path: str) -> Optional[str]:
        """使用 sherpa-onnx 识别"""
        try:
            import sherpa_onnx
            import numpy as np
            import wave
            
            with wave.open(wav_path, "r") as f:
                frames = f.readframes(f.getnframes())
                samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            stream = self.engine.create_stream()
            stream.accept_waveform(16000, samples)
            
            # 加入尾部静音触发识别结束
            tail_paddings = np.zeros(int(0.66 * 16000), dtype=np.float32)
            stream.accept_waveform(16000, tail_paddings)
            stream.input_finished()
            
            while self.engine.is_ready(stream):
                self.engine.decode_stream(stream)
            
            result = self.engine.get_result(stream)
            return result.text.strip() if result.text else None
        
        except Exception as e:
            logger.error(f"❌ sherpa-onnx 识别失败: {e}")
            return None
    
    def _recognize_faster_whisper(self, wav_path: str) -> Optional[str]:
        """使用 faster-whisper 识别"""
        try:
            segments, _ = self.engine.transcribe(
                wav_path,
                language="zh",
                beam_size=1,
                vad_filter=True,
            )
            
            text = " ".join(segment.text for segment in segments).strip()
            return text if text else None
        
        except Exception as e:
            logger.error(f"❌ faster-whisper 识别失败: {e}")
            return None
    
    async def recognize_from_url(self, url: str) -> Optional[str]:
        """
        从 URL 下载音频并识别
        
        Args:
            url: 音频文件 URL
            
        Returns:
            识别出的文字
        """
        try:
            import aiohttp
            import tempfile
            import os
            
            # 下载音频
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        return None
                    
                    # 获取文件后缀
                    content_type = resp.headers.get("Content-Type", "")
                    ext = ".ogg" if "ogg" in content_type else ".mp3"
                    
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                        tmp.write(await resp.read())
                        tmp_path = tmp.name
            
            # 识别
            result = await self.recognize(tmp_path)
            
            # 清理临时文件
            os.remove(tmp_path)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 从 URL 识别失败: {e}")
            return None
