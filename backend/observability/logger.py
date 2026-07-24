import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path, log_level: str = "INFO"):
    """
    配置全局日志系统
    :param log_dir: 日志文件存放目录
    :param log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 确保目录存在
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "system.log"

    # 1. 清除所有默认处理器
    logger.remove()

    # 2. 配置控制台输出 (带颜色和精简格式)
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True,  # 异步写入，不阻塞主线程
    )

    # 3. 配置本地文件输出 (自动滚动与保留)
    logger.add(
        str(log_file),
        rotation="10 MB",  # 日志满 10MB 自动切分
        retention="7 days",  # 仅保留最近 7 天的日志
        level=log_level,
        encoding="utf-8",
        compression="zip",  # 旧日志自动压缩成 zip 节省空间
        enqueue=True,
    )

    # 4. 注册全局未捕获异常钩子
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        """
        拦截系统级崩溃，将其记录到日志中，而不是简单的闪退
        """
        # 忽略用户手动中断 (Ctrl+C)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 使用 loguru 的 exception 选项自动格式化完整的堆栈信息
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("💥 系统由于未捕获的严重异常而崩溃")

    # 将自定义钩子绑定到系统
    sys.excepthook = handle_unhandled_exception

    logger.info(f"✨ 日志系统初始化完毕，级别: {log_level}，日志目录: {log_dir}")


# 🚀 统一导出别名，方便旧代码平替
sys_logger = logger

__all__ = ["setup_logger", "sys_logger"]
