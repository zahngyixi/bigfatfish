# -*- coding: utf-8 -*-
"""
记忆管理器
统一管理短期记忆（Redis）和长期记忆（ChromaDB）
"""
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..memory.redis_cache import RedisCache
from ..memory.chromadb_store import ChromaDBStore
from ..memory.memory_extractor import MemoryExtractor
from ..config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """统一记忆管理器"""
    
    def __init__(self):
        """初始化记忆管理器"""
        self.redis_cache = RedisCache()
        self.chromadb_store = ChromaDBStore()
        self.memory_extractor = MemoryExtractor()
        
        logger.info("✓ 记忆管理器初始化成功")
    
    async def add_to_short_memory(self, user_id: str, message: Dict[str, str]):
        """
        添加消息到短期记忆
        
        Args:
            user_id: 用户 ID
            message: 消息对象 {"role": "user/assistant", "content": "..."}
        """
        await self.redis_cache.add_message(user_id, message)
    
    async def get_short_context(self, user_id: str, window_size: int = 10) -> List[Dict[str, str]]:
        """
        获取短期对话上下文
        
        Args:
            user_id: 用户 ID
            window_size: 窗口大小（轮数）
            
        Returns:
            消息列表
        """
        return await self.redis_cache.get_recent_messages(user_id, window_size * 2)
    
    async def extract_and_store_long_memory(self, user_id: str):
        """
        从短期记忆中提取关键信息并存入长期记忆
        
        Args:
            user_id: 用户 ID
        """
        # 获取最近的对话
        recent_messages = await self.redis_cache.get_recent_messages(user_id, limit=20)
        if not recent_messages:
            logger.debug(f"用户 {user_id} 无短期记忆，跳过提取")
            return
        
        # 格式化对话内容
        conversation = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])
        
        # 调用提取器
        extracted_facts = await self.memory_extractor.extract(conversation)
        
        # 存入 ChromaDB
        for fact in extracted_facts:
            await self.chromadb_store.add_memory(
                user_id=user_id,
                content=fact["content"],
                category=fact.get("category", "general"),
                importance=fact.get("importance", 3),
                metadata={
                    "timestamp": fact.get("timestamp", datetime.now().isoformat()),
                    "source": "auto_extract"
                }
            )
        
        logger.info(f"✓ 为用户 {user_id} 提取了 {len(extracted_facts)} 条长期记忆")
    
    async def retrieve_relevant_memory(self, query: str, user_id: str, top_k: int = 5) -> str:
        """
        检索相关的长期记忆
        
        Args:
            query: 查询文本（通常是用户当前消息）
            user_id: 用户 ID
            top_k: 返回最相关的 K 条记忆
            
        Returns:
            格式化的记忆文本
        """
        results = await self.chromadb_store.search_memory(user_id, query, top_k)
        
        if not results:
            return ""
        
        # 格式化记忆内容
        memory_lines = []
        for i, result in enumerate(results, 1):
            memory_lines.append(f"{i}. {result['content']} (重要度: {result.get('importance', 3)})")
        
        return "\n".join(memory_lines)
    
    async def clear_short_memory(self, user_id: str):
        """清空用户的短期记忆"""
        await self.redis_cache.clear_user_messages(user_id)
        logger.info(f"✓ 已清空用户 {user_id} 的短期记忆")
    
    async def get_user_stats(self, user_id: str) -> Dict[str, int]:
        """
        获取用户记忆统计
        
        Returns:
            {"short_memory_count": N, "long_memory_count": M}
        """
        short_count = await self.redis_cache.get_message_count(user_id)
        long_count = await self.chromadb_store.count_memories(user_id)
        
        return {
            "short_memory_count": short_count,
            "long_memory_count": long_count
        }
