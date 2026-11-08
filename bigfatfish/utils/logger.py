# -*- coding: utf-8 -*-
"""
工具函数库
"""
import logging
import sys
from pathlib import Path
from ..config import settings


def setup_logging():
    """配置全局日志系统"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    log_path = Path(settings.LOG_PATH)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    fmt = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)
    
    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 文件 handler
    file_handler = logging.FileHandler(
        str(log_path / "bigfatfish.log"),
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    
    # 根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger
