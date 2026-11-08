# -*- coding: utf-8 -*-
"""
情绪与表情包系统
根据 AI 回复中的情绪标签，随机选取对应分类的表情包发送
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, List

from ..config import settings

logger = logging.getLogger(__name__)

# 情绪标签 -> 表情包目录 映射
EMOTION_DIR_MAP = {
    "happy":   "happy",
    "sad":     "sad",
    "angry":   "angry",
    "cute":    "cute",
    "neutral": "neutral",
    "anxious": "sad",
}

# 支持的图片格式
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class EmotionSystem:
    """表情包 + 情绪系统"""
    
    def __init__(self):
        """初始化表情包系统"""
        self.base_path = Path(settings.EMOTICON_PATH)
        self._emoticon_cache: Dict[str, List[str]] = {}
        
        # 建立索引
        self._index_emoticons()
        logger.info(f"✓ 表情包系统初始化完成 ({sum(len(v) for v in self._emoticon_cache.values())} 张图片)")
    
    def _index_emoticons(self):
        """索引表情包目录"""
        if not self.base_path.exists():
            logger.warning(f"⚠ 表情包目录不存在: {self.base_path}")
            return
        
        for emotion, dir_name in EMOTION_DIR_MAP.items():
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                imgs = [
                    str(f)
                    for f in dir_path.iterdir()
                    if f.suffix.lower() in IMG_EXTENSIONS
                ]
                self._emoticon_cache[emotion] = imgs
                logger.debug(f"  {emotion}: {len(imgs)} 张")
    
    async def get_emoticon(self, emotion: str, probability: float = 0.6) -> Optional[str]:
        """
        根据情绪随机获取一张表情包
        
        Args:
            emotion: 情绪标签 (happy/sad/angry/cute/neutral)
            probability: 触发概率（不是每次都发，避免刷屏）
            
        Returns:
            表情包图片路径，None 表示不发送
        """
        # 概率控制
        if random.random() > probability:
            return None
        
        # 映射情绪到目录
        mapped_emotion = EMOTION_DIR_MAP.get(emotion.lower(), "neutral")
        imgs = self._emoticon_cache.get(mapped_emotion, [])
        
        if not imgs:
            logger.debug(f"⚠ 情绪 '{emotion}' 没有对应的表情包")
            return None
        
        selected = random.choice(imgs)
        logger.debug(f"✓ 选中表情包: {Path(selected).name} (情绪: {emotion})")
        return selected
    
    def add_emoticon(self, emotion: str, image_path: str) -> bool:
        """
        动态添加表情包
        
        Args:
            emotion: 情绪标签
            image_path: 图片路径
            
        Returns:
            是否添加成功
        """
        target_dir = self.base_path / EMOTION_DIR_MAP.get(emotion, "neutral")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        src = Path(image_path)
        if not src.exists():
            return False
        
        # 复制图片到对应目录
        dst = target_dir / src.name
        import shutil
        shutil.copy2(str(src), str(dst))
        
        # 更新索引
        mapped = EMOTION_DIR_MAP.get(emotion, "neutral")
        if mapped not in self._emoticon_cache:
            self._emoticon_cache[mapped] = []
        self._emoticon_cache[mapped].append(str(dst))
        
        logger.info(f"✓ 添加表情包: {src.name} ({emotion})")
        return True
    
    def get_stats(self) -> Dict[str, int]:
        """获取表情包统计"""
        return {
            emotion: len(imgs)
            for emotion, imgs in self._emoticon_cache.items()
        }
