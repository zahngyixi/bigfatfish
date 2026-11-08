# -*- coding: utf-8 -*-
"""
DeepSeek AI Agent 核心模块
处理与 DeepSeek API 的所有交互，支持流式输出和上下文管理
"""
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime

try:
    import aiohttp
    import httpx
except ImportError:
    aiohttp = None
    httpx = None

from ..config import settings, PromptTemplates
from .context_compressor import ContextCompressor
from .memory_manager import MemoryManager

# 导入鲸鱼娘人格配置
try:
    from .whale_persona import get_whale_system_prompt
    WHALE_PERSONA_AVAILABLE = True
except ImportError:
    WHALE_PERSONA_AVAILABLE = False
    get_whale_system_prompt = None


logger = logging.getLogger(__name__)


class DeepSeekAgent:
    """DeepSeek AI Agent 主类"""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        初始化 DeepSeek Agent
        
        Args:
            memory_manager: 记忆管理器实例（可选）
        """
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = settings.DEEPSEEK_MODEL
        self.max_tokens = settings.DEEPSEEK_MAX_TOKENS
        self.temperature = settings.DEEPSEEK_TEMPERATURE
        self.stream = settings.DEEPSEEK_STREAM
        
        self.memory_manager = memory_manager
        self.context_compressor = ContextCompressor()
        self.conversation_turn = 0
        
        logger.info(f"✓ DeepSeek Agent 初始化成功 (Model: {self.model})")
    
    async def chat_stream(
        self,
        user_message: str,
        user_id: str,
        platform: str = "default",
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话处理
        
        Args:
            user_message: 用户消息
            user_id: 用户 ID（用于记忆检索）
            platform: 平台名称（qq/bilibili/default）
            system_prompt: 自定义系统提示（如为空则使用默认人设）
            
        Yields:
            流式回复内容
        """
        try:
            # ========== 步骤 1: 检索长期记忆 ==========
            long_term_memory = ""
            if self.memory_manager:
                long_term_memory = await self.memory_manager.retrieve_relevant_memory(
                    user_message,
                    user_id,
                    top_k=settings.LONG_MEMORY_TOP_K
                )
            
            # ========== 步骤 2: 构建完整 Prompt ==========
            if system_prompt is None:
                # 如果配置启用鲸鱼娘人格，使用鲸鱼娘 prompt
                if WHALE_PERSONA_AVAILABLE and settings.USE_WHALE_PERSONA:
                    system_prompt = get_whale_system_prompt()
                else:
                    system_prompt = PromptTemplates.SYSTEM_PERSONA
            
            # 从记忆中获取短期对话上下文
            short_context = []
            if self.memory_manager:
                short_context = await self.memory_manager.get_short_context(
                    user_id,
                    window_size=settings.SHORT_MEMORY_WINDOW
                )
            
            # 构建最终的 messages 列表
            messages = PromptTemplates.build_chat_prompt(
                system_prompt,
                long_term_memory,
                short_context
            )
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # ========== 步骤 3: 调用 DeepSeek API 流式接口 ==========
            async for chunk in self._call_deepseek_stream(messages):
                yield chunk
            
            self.conversation_turn += 1
            
            # ========== 步骤 4: 异步更新记忆 (非阻塞) ==========
            if self.memory_manager:
                asyncio.create_task(
                    self._update_memory_async(
                        user_id,
                        user_message,
                        platform,
                        self.conversation_turn
                    )
                )
        
        except Exception as e:
            logger.error(f"❌ 流式对话出错: {e}")
            yield f"[错误] 处理失败: {str(e)}"
    
    async def chat(
        self,
        user_message: str,
        user_id: str,
        platform: str = "default",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        单次对话（非流式）
        
        Returns:
            完整回复文本
        """
        full_response = ""
        async for chunk in self.chat_stream(user_message, user_id, platform, system_prompt):
            full_response += chunk
        return full_response
    
    async def _call_deepseek_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        调用 DeepSeek API 流式接口
        
        Args:
            messages: OpenAI 格式的 messages 列表
            
        Yields:
            流式回复文本片段
        """
        if not aiohttp:
            logger.warning("⚠ aiohttp 未安装，切换为同步模式")
            async for chunk in self._call_deepseek_stream_sync(messages):
                yield chunk
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"DeepSeek API 错误 ({resp.status}): {error_text}")
                        yield f"[API 错误] {resp.status}: {error_text}"
                        return
                    
                    async for line in resp.content:
                        line = line.decode('utf-8').strip()
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data:'):
                            line = line[5:].strip()
                            if line == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(line)
                                if data.get('choices'):
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                logger.debug(f"无法解析 JSON: {line}")
                                continue
        
        except asyncio.TimeoutError:
            logger.error("❌ DeepSeek API 请求超时")
            yield "[超时] 请求超时，请稍后重试"
        except Exception as e:
            logger.error(f"❌ API 调用异常: {e}")
            yield f"[异常] {str(e)}"
    
    async def _call_deepseek_stream_sync(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        备用同步方式（httpx）
        """
        if not httpx:
            yield "[错误] httpx 库未安装"
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        
        try:
            with httpx.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
                timeout=300,
            ) as response:
                if response.status_code != 200:
                    yield f"[API 错误] {response.status_code}"
                    return
                
                for line in response.iter_lines():
                    if not line or line.startswith(':'):
                        continue
                    
                    if line.startswith('data:'):
                        line = line[5:].strip()
                        if line == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(line)
                            if data.get('choices'):
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"❌ 同步调用异常: {e}")
            yield f"[异常] {str(e)}"
    
    async def _update_memory_async(self, user_id: str, user_message: str, platform: str, turn: int):
        """
        异步更新记忆（非阻塞）
        每 MEMORY_EXTRACT_INTERVAL 轮提取一次长期记忆
        """
        if not self.memory_manager:
            return
        
        try:
            # 添加到短期记忆
            await self.memory_manager.add_to_short_memory(
                user_id,
                {"role": "user", "content": user_message},
            )
            
            # 每 N 轮提取一次长期记忆
            if turn % settings.MEMORY_EXTRACT_INTERVAL == 0:
                logger.info(f"📝 正在为用户 {user_id} 提取长期记忆...")
                await self.memory_manager.extract_and_store_long_memory(user_id)
        
        except Exception as e:
            logger.error(f"❌ 记忆更新失败: {e}")
