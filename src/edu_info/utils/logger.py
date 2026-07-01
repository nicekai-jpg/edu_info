"""日志配置模块"""
import logging
import sys


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    设置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 创建控制台 handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # 添加 handler
    logger.addHandler(handler)

    return logger


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    获取日志记录器（兼容性别名）
    """
    return setup_logger(name, level)


def setup_global_logger(level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    """
    设置全局日志配置（兼容性别名）
    """
    return setup_logger("root", level)
