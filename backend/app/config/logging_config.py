import logging
import logging.config
import os
from pathlib import Path

def setup_logging():
    """设置日志配置"""
    
    # 获取项目根目录（backend目录）
    # 从当前文件位置向上两级到达backend目录
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent.parent  # app/config -> app -> backend
    log_dir = backend_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 日志配置
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(log_dir / 'app.log'),  # 使用绝对路径
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': str(log_dir / 'error.log'),  # 使用绝对路径
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'import_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(log_dir / 'import.log'),  # 使用绝对路径
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            # 根日志器
            '': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            # 应用日志器
            'app': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False
            },
            # 导入相关日志器
            'app.utils.enhanced_data_processor': {
                'handlers': ['console', 'file', 'import_file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'app.api.v1.routes.enhanced_import': {
                'handlers': ['console', 'file', 'import_file'],
                'level': 'DEBUG',
                'propagate': False
            },
            # Elasticsearch日志器
            'app.utils.elasticsearch': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            # 第三方库日志控制
            'elasticsearch': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False
            },
            'urllib3': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # 应用日志配置
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 记录启动信息
    logger = logging.getLogger('app')
    logger.info("=" * 50)
    logger.info("海关数据管理系统启动")
    logger.info(f"日志目录: {log_dir.absolute()}")
    logger.info("=" * 50)

def get_logger(name: str = None):
    """获取日志器"""
    if name is None:
        name = 'app'
    return logging.getLogger(name)