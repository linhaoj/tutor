"""日志配置模块"""
import logging
import sys
from datetime import datetime
from pathlib import Path

# 创建logs目录
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    创建并配置logger

    Args:
        name: logger名称（通常是模块名）
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 控制台输出handler - 只显示INFO及以上
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt=DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)

    # 文件输出handler - 记录所有级别
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        LOGS_DIR / f"app_{today}.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    # 错误日志单独记录
    error_handler = logging.FileHandler(
        LOGS_DIR / f"error_{today}.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # 添加所有handler
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger


# 创建默认logger
default_logger = setup_logger("app")


# 便捷函数
def get_logger(name: str = "app") -> logging.Logger:
    """获取logger实例"""
    return setup_logger(name)
