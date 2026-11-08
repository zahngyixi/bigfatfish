# -*- coding: utf-8 -*-
"""
上下文压缩器
自动管理对话上下文，防止 Token 超限
"""
import logging
from typing import List, Dict
from ..config import settings, PromptTemplates

logger = logging.getLogger(__name__)


class ContextCompressor:
    """上下文压缩管理器"""
    
    def __init__(self, max_context_tokens: int = 4000):
        """
        初始化压缩器
        
        Args:
            max_context_tokens: 最大上下文 Token 数（粗略估算）
        """
        self.max_context_tokens = max_context_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """
        粗略估算文本的 Token 数量
        中文：1字 ≈ 1.5 tokens
        英文：1词 ≈ 1.3 tokens
        
        Args:
            text: 文本内容
            
        Returns:
            估算的 Token 数
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.3)
    
    def should_compress(self, messages: List[Dict[str, str]]) -> bool:
        """
        判断是否需要压缩上下文
        
        Args:
            messages: 消息列表
            
        Returns:
            是否需要压缩
        """
        total_tokens = sum(
            self.estimate_tokens(msg.get("content", ""))
            for msg in messages
        )
        return total_tokens > self.max_context_tokens
    
    def compress_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        压缩对话上下文
        保留系统提示 + 最近 N 轮对话
        
        Args:
            messages: 原始消息列表
            
        Returns:
            压缩后的消息列表
        """
        if not self.should_compress(messages):
            return messages
        
        logger.info("📦 开始压缩上下文...")
        
        # 保留系统消息
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        
        # 保留最近的对话
        recent_messages = [msg for msg in messages if msg.get("role") != "system"]
        recent_messages = recent_messages[-settings.SHORT_MEMORY_WINDOW * 2:]  # 保留最近 N 轮（用户+助手）
        
        compressed = system_messages + recent_messages
        
        logger.info(f"✓ 上下文压缩完成: {len(messages)} -> {len(compressed)} 条消息")
        return compressed
