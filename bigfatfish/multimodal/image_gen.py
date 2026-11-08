# -*- coding: utf-8 -*-
"""
文生图模块
支持 HuggingFace Inference API (免费，无需本地 GPU)
在 ARM64 Termux 上完全通过 HTTP API 调用，无需本地 CUDA
"""
import logging
import asyncio
import time
from pathlib import Path
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    文生图生成器
    
    ARM64 Termux 兼容方案（全部为 API 调用，无需本地 GPU）:
    ─────────────────────────────────────────────────────────────────
    ✅ 方案一: HuggingFace Inference API (免费，推荐)
       模型: stabilityai/stable-diffusion-xl-base-1.0
       限额: 每天若干免费请求
       配置: IMAGE_GEN_API_URL=https://api-inference.huggingface.co/models/...
    
    ✅ 方案二: SD WebUI API (本地/局域网 SD)
       如果用户在 PC 上运行了 SD WebUI，手机可通过局域网调用
       配置: IMAGE_GEN_API_URL=http://192.168.1.x:7860
    
    ✅ 方案三: Pollinations.AI (完全免费，无需 API Key)
       配置: IMAGE_GEN_API_URL=https://image.pollinations.ai
    ─────────────────────────────────────────────────────────────────
    """
    
    OUTPUT_DIR = Path(settings.LOG_PATH).parent / "generated_images"
    
    def __init__(self):
        """初始化生成器"""
        self.api_url = settings.IMAGE_GEN_API_URL
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        if settings.IMAGE_GEN_ENABLED:
            self._detect_backend()
    
    def _detect_backend(self):
        """检测后端类型"""
        if not self.api_url:
            logger.warning("⚠ IMAGE_GEN_API_URL 未配置")
            return
        
        if "huggingface.co" in self.api_url:
            self.backend = "huggingface"
        elif "pollinations.ai" in self.api_url:
            self.backend = "pollinations"
        else:
            self.backend = "sd_webui"  # 假设为 SD WebUI API
        
        logger.info(f"✓ 文生图后端: {self.backend}")
    
    async def generate(self, prompt: str) -> Optional[str]:
        """
        根据 Prompt 生成图片
        
        Args:
            prompt: 图片描述
            
        Returns:
            生成图片的路径，失败返回 None
        """
        if not settings.IMAGE_GEN_ENABLED:
            logger.debug("⚠ 文生图功能未启用")
            return None
        
        if not self.api_url:
            return None
        
        logger.info(f"🎨 开始生成图片: {prompt[:50]}...")
        
        try:
            # 自动翻译中文 Prompt（大多数 SD 模型对英文 Prompt 效果更好）
            en_prompt = await self._translate_prompt(prompt)
            
            if self.backend == "huggingface":
                return await self._generate_huggingface(en_prompt)
            elif self.backend == "pollinations":
                return await self._generate_pollinations(en_prompt or prompt)
            elif self.backend == "sd_webui":
                return await self._generate_sd_webui(en_prompt)
        
        except Exception as e:
            logger.error(f"❌ 图片生成失败: {e}")
            return None
    
    async def _translate_prompt(self, text: str) -> str:
        """将中文 Prompt 翻译为英文（调用 DeepSeek 翻译）"""
        try:
            import aiohttp as _aiohttp
            
            async with _aiohttp.ClientSession() as session:
                payload = {
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": "Translate the following Chinese description to an English Stable Diffusion prompt. Return ONLY the translated prompt, no explanations."},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 200,
                    "stream": False
                }
                
                async with session.post(
                    f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                    timeout=_aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
        
        except Exception:
            pass
        
        return text  # 翻译失败则原文返回
    
    async def _generate_huggingface(self, prompt: str) -> Optional[str]:
        """HuggingFace Inference API 生成图片"""
        headers = {}
        
        hf_token = os.environ.get("HF_TOKEN", "")
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        
        payload = {"inputs": prompt}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"❌ HuggingFace API 返回: {resp.status}")
                    return None
                
                image_bytes = await resp.read()
                return self._save_image(image_bytes, "hf")
    
    async def _generate_pollinations(self, prompt: str) -> Optional[str]:
        """
        Pollinations.AI 完全免费，无需 API Key
        直接 GET 请求即可获取图片
        """
        import urllib.parse
        
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    return None
                
                image_bytes = await resp.read()
                return self._save_image(image_bytes, "pollinations")
    
    async def _generate_sd_webui(self, prompt: str) -> Optional[str]:
        """SD WebUI API（txt2img 接口）"""
        api_url = f"{self.api_url.rstrip('/')}/sdapi/v1/txt2img"
        
        payload = {
            "prompt": prompt,
            "negative_prompt": "nsfw, blurry, bad quality",
            "steps": 20,
            "width": 512,
            "height": 512,
            "cfg_scale": 7,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                images = data.get("images", [])
                
                if not images:
                    return None
                
                # Base64 解码
                import base64
                image_bytes = base64.b64decode(images[0])
                return self._save_image(image_bytes, "sd")
    
    def _save_image(self, image_bytes: bytes, prefix: str = "gen") -> str:
        """保存图片文件"""
        output_path = self.OUTPUT_DIR / f"{prefix}_{int(time.time())}.png"
        output_path.write_bytes(image_bytes)
        logger.info(f"✓ 图片已保存: {output_path}")
        return str(output_path)


import os  # 补充缺失的 import
