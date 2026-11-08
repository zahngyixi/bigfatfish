# -*- coding: utf-8 -*-
"""
频率控制器
防止消息过于频繁，避免被平台风控
"""
import time
import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict

from ..config import settings

logger = logging.getLogger(__name__)


class FrequencyController:
    """频率控制器"""
    
    def __init__(self):
        """初始化频控"""
        # 记录每个用户上次回复时间
        self._last_reply_time: Dict[str, float] = {}
        # 滑动窗口（过去 60 秒的回复次数）
        self._reply_window: Dict[str, deque] = defaultdict(deque)
        
        # 最小间隔秒数
        self.min_interval = settings.FREQUENCY_LIMIT_SECONDS
        # 每分钟最大回复数
        self.max_per_minute = settings.MAX_REPLY_PER_MINUTE
    
    async def check(self, key: str) -> bool:
        """
        检查是否允许回复
        
        Args:
            key: 用户/群 唯一标识
            
        Returns:
            True = 允许回复，False = 触发限制
        """
        now = time.time()
        
        # ========== 检查最小间隔 ==========
        last_time = self._last_reply_time.get(key, 0)
        if now - last_time < self.min_interval:
            elapsed = now - last_time
            logger.debug(f"频率限制: 距离上次回复仅 {elapsed:.1f}s < {self.min_interval}s")
            return False
        
        # ========== 检查每分钟频率 ==========
        window = self._reply_window[key]
        
        # 清除超过 60 秒的记录
        while window and now - window[0] > 60:
            window.popleft()
        
        if len(window) >= self.max_per_minute:
            logger.warning(f"⚠ 用户 {key} 每分钟回复超过 {self.max_per_minute} 次，触发限制")
            return False
        
        # ========== 记录本次回复 ==========
        self._last_reply_time[key] = now
        window.append(now)
        
        return True
    
    def reset(self, key: str):
        """重置用户的频控记录"""
        if key in self._last_reply_time:
            del self._last_reply_time[key]
        if key in self._reply_window:
            del self._reply_window[key]
