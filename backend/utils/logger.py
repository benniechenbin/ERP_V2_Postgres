import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys

# 1. 确保日志目录存在 (我们把它放在和 uploads 同级的 data/logs 目录下)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "erp_system.log"
# =========================================================
# 🛡️ 专治 Windows 终端 GBK 乱码/崩溃问题
# 强行将标准输出流重置为 UTF-8 编码，让火箭 🚀 顺利升空！
# =========================================================
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
def setup_logger():
    """初始化全局日志记录器"""
    # 如果已经配置过，直接返回，防止重复打印
    logger = logging.getLogger("ERP_CORE")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 2. 定义高可读性的日志格式
    # 格式: [2026-03-22 10:15:30] [ERROR] [db_engine.py:42] -> 数据库连接失败
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] -> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. 落地到文件：设置日志轮转 (单文件最大 10MB，最多保留 5 个备份)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 4. 同时输出到控制台 (方便你在本地或 Docker logs 里看)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 暴露出全局单例 logger
sys_logger = setup_logger()

# 文件位置: backend/utils/logger.py (追加在文件末尾)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """
    全局异常拦截器：专门抓捕那些没有被 try...except 兜住的致命崩溃！
    """
    # 忽略 Ctrl+C 导致的程序中断，不当做报错记录
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 🚨 将系统崩溃级别的报错，强制写入黑匣子！
    sys_logger.critical("💥 [致命崩溃] 发现未捕获的系统级异常！", exc_info=(exc_type, exc_value, exc_traceback))

# 替换 Python 默认的崩溃处理机制
sys.excepthook = handle_unhandled_exception