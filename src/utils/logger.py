"""
日志系统模块
提供统一的日志记录功能
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name: str, log_file: str = None, log_level: str = "INFO") -> logging.Logger:
    """
    设置并返回一个配置好的logger
    
    Args:
        name (str): logger名称
        log_file (str): 日志文件路径，如果为None则使用默认路径
        log_level (str): 日志级别
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    logger.setLevel(level_map.get(log_level.upper(), logging.INFO))
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file is None:
        # 使用默认路径
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"tiaozhanbei2_{datetime.now().strftime('%Y%m%d')}.log")
    
    try:
        # 创建文件处理器（带轮转）
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    获取logger实例
    
    Args:
        name (str): logger名称，如果为None则使用调用模块名
        
    Returns:
        logging.Logger: logger实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return setup_logger(name)

class LoggerMixin:
    """
    日志混合类，为其他类提供日志功能
    """
    
    @property
    def logger(self):
        """获取logger实例"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

# 便捷函数
def debug(msg, *args, **kwargs):
    """记录DEBUG级别日志"""
    get_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """记录INFO级别日志"""
    get_logger().info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """记录WARNING级别日志"""
    get_logger().warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """记录ERROR级别日志"""
    get_logger().error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    """记录CRITICAL级别日志"""
    get_logger().critical(msg, *args, **kwargs)

# 创建默认logger
default_logger = setup_logger("Tiaozhanbei2.0")

if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger("test")
    logger.debug("这是一个调试消息")
    logger.info("这是一个信息消息")
    logger.warning("这是一个警告消息")
    logger.error("这是一个错误消息")
    logger.critical("这是一个严重错误消息")
