"""日志配置模块"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = 'Lotto3D', level: int = logging.INFO, log_file: str = None) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        name: 日志名称
        level: 日志级别
        log_file: 日志文件路径
        
    Returns:
        配置好的logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的handlers
    logger.handlers.clear()
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler
    if log_file is None:
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"lottery3d_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
