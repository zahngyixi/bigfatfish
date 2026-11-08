# -*- coding: utf-8 -*-
"""
Redis 缓存层 - 短期记忆
存储最近 N 轮对话上下文
支持 ARM64 Termux 环境
"""
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

try:
    import redis
    import aioredis
except ImportError:
    redis = None
    aioredis = None

from ..config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 缓存管理器（短期记忆）"""
    
    def __init__(self):
        """初始化 Redis 连接"""
        self.redis = None
        self.async_redis = None
        self._init_redis()
    
    def _init_redis(self):
        """初始化 Redis 连接"""
        try:
            if redis:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                )
                # 测试连接
                self.redis.ping()
                logger.info("✓ Redis 连接成功")
            else:
                logger.warning("⚠ redis 未安装，使用内存缓存")
                self._use_memory_cache()
        except Exception as e:
            logger.warning(f"⚠ Redis 连接失败 ({e})，切换到内存缓存")
            self._use_memory_cache()
    
    def _use_memory_cache(self):
        """切换到内存缓存（备用方案）"""
        self.memory_storage = {}
    
    async def add_message(self, user_id: str, message: Dict[str, str]):
        """
        添加消息到用户的对话历史
        
        Args:
            user_id: 用户 ID
            message: 消息 {"role": "user/assistant", "content": "..."}
        """
        try:
            if not self.redis:
                # 内存缓存模式
                if user_id not in self.memory_storage:
                    self.memory_storage[user_id] = []
                self.memory_storage[user_id].append({
                    **message,
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Redis 模式
            key = f"chat:{user_id}"
            message_with_ts = {
                **message,
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用 Redis List 存储（LPUSH 添加到头部）
            self.redis.lpush(key, json.dumps(message_with_ts, ensure_ascii=False))
            
            # 设置过期时间 (7 天)
            self.redis.expire(key, 7 * 24 * 3600)
            
            logger.debug(f"✓ 消息已添加到 Redis (用户: {user_id})")
        
        except Exception as e:
            logger.error(f"❌ 添加消息失败: {e}")
    
    async def get_recent_messages(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        获取用户最近的对话消息
        
        Args:
            user_id: 用户 ID
            limit: 最大消息数
            
        Returns:
            消息列表（按时间顺序）
        """
        try:
            if not self.redis:
                # 内存缓存模式
                if user_id not in self.memory_storage:
                    return []
                messages = self.memory_storage[user_id][-limit:]
                return [{"role": m["role"], "content": m["content"]} for m in messages]
            
            # Redis 模式
            key = f"chat:{user_id}"
            raw_messages = self.redis.lrange(key, 0, limit - 1)
            
            messages = []
            for raw_msg in reversed(raw_messages):  # 反转以获得正确的时间顺序
                try:
                    msg = json.loads(raw_msg)
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                except json.JSONDecodeError:
                    logger.debug(f"无法解析消息: {raw_msg}")
            
            return messages
        
        except Exception as e:
            logger.error(f"❌ 获取消息失败: {e}")
            return []
    
    async def get_message_count(self, user_id: str) -> int:
        """获取用户消息总数"""
        try:
            if not self.redis:
                if user_id not in self.memory_storage:
                    return 0
                return len(self.memory_storage[user_id])
            
            key = f"chat:{user_id}"
            return self.redis.llen(key)
        
        except Exception as e:
            logger.error(f"❌ 获取消息计数失败: {e}")
            return 0
    
    async def clear_user_messages(self, user_id: str):
        """清空用户的所有消息"""
        try:
            if not self.redis:
                if user_id in self.memory_storage:
                    del self.memory_storage[user_id]
                return
            
            key = f"chat:{user_id}"
            self.redis.delete(key)
            logger.info(f"✓ 已清空用户 {user_id} 的消息记录")
        
        except Exception as e:
            logger.error(f"❌ 清空消息失败: {e}")
