# -*- coding: utf-8 -*-
"""
记忆提取器
使用大模型从对话中自动提取关键事实
"""
import json
import logging
from typing import List, Dict

from ..config import PromptTemplates

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """记忆提取器"""
    
    async def extract(self, conversation: str) -> List[Dict]:
        """
        从对话中提取关键信息
        
        Args:
            conversation: 对话文本
            
        Returns:
            提取的事实列表
        """
        # 这里需要调用 DeepSeek API 来提取记忆
        # 为了避免循环依赖，我们延迟导入
        from ..core import DeepSeekAgent
        
        try:
            agent = DeepSeekAgent()
            
            # 构建提取 Prompt
            extract_prompt = PromptTemplates.MEMORY_EXTRACT_PROMPT.format(
                conversation=conversation
            )
            
            # 调用 API
            import asyncio
            
            # 由于 API 是异步的，我们需要在这里创建一个临时的 event loop
            result_text = ""
            async for chunk in agent.chat_stream(
                extract_prompt,
                user_id="system",
                system_prompt="你是一个专业的信息提取系统。请提取关键信息并返回 JSON 格式的结果。"
            ):
                result_text += chunk
            
            # 解析 JSON
            try:
                facts = json.loads(result_text)
                if isinstance(facts, list):
                    logger.info(f"✓ 提取了 {len(facts)} 条记忆")
                    return facts
            except json.JSONDecodeError:
                logger.warning(f"⚠ 无法解析提取结果的 JSON: {result_text[:100]}")
                return []
        
        except Exception as e:
            logger.error(f"❌ 记忆提取失败: {e}")
            return []
