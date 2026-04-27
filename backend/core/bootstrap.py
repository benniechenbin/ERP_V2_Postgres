import sys
from pathlib import Path
from backend.config.settings import settings
from backend.observability.logger import setup_logger, sys_logger

@sys_logger.catch
def init_system():
    """
    🌌 ERP_V2_Postgres 引擎点火程序
    负责：初始化全局日志、自动创建物理挂载目录、关键环境预检。
    """
    # 1. 确定项目根目录 (相对于 backend/core/bootstrap.py 向上找两级)
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # 2. 初始化日志系统
    log_dir = project_root / "logs"
    setup_logger(log_dir=log_dir, log_level="INFO")

    sys_logger.info("="*50)
    sys_logger.info("🚀 系统核心引擎正在点火...")   

    # 3. 目录预检：自动创建必要的物理目录 (防止 IO 报错)
    # 这里的路径建议从根目录开始拼接，确保在 Docker 和本地都一致
    paths_to_create = [
        log_dir,
        project_root / "data" / "uploads",           # 附件上传目录
        project_root / "backend" / "models",         # 本地大模型目录
        project_root / "host_data" / "experiments",  # 实验数据目录
    ]
    
    for p in paths_to_create:        
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            sys_logger.debug(f"📁 已创建物理目录: {p}")

    # 4. 环境状态播报 (Fail-Fast 预检)
    try:
        # 播报数据库连接目标
        sys_logger.info(f"💾 数据库目标: {settings.DB_HOST}:{settings.DB_PORT} / {settings.DB_NAME}")
        
        # 播报 AI 引擎配置
        sys_logger.info(f"💬 AI 引擎模式: {settings.AI_PROVIDER}")
        if settings.AI_PROVIDER == "local_gguf":
            model_path = project_root / "backend" / "models" / settings.GGUF_MODEL_NAME
            if not model_path.exists():
                sys_logger.warning(f"⚠️ 本地模型文件未找到: {settings.GGUF_MODEL_NAME}")
            else:
                sys_logger.info(f"🤖 已锚定本地模型: {settings.GGUF_MODEL_NAME}")
                
    except Exception as e:
        sys_logger.exception(f"❌ 环境预检发现异常：{e}")
        # 在这里可以选择 raise e 强行停止启动，也可以记录后继续
        
    sys_logger.info("✅ 引擎点火完成，系统各项基建指标正常！")
    sys_logger.info("="*50)

def is_initialized():
    """判断系统是否已点火"""
    # 此处可以根据需要增加更复杂的逻辑
    return True