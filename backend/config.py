"""
应用配置文件

版权所有 (c) 2025 赵宏宇
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """基础配置"""
    
    # 密钥配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f'sqlite:///{BASE_DIR / "database" / "voting.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传配置
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    PHOTO_FOLDER = UPLOAD_FOLDER / 'photos'
    FILE_FOLDER = UPLOAD_FOLDER / 'files'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'csv'}
    
    # WiFi热点配置
    HOTSPOT_SSID = os.getenv('HOTSPOT_SSID', '投票抽奖系统')
    HOTSPOT_PASSWORD = os.getenv('HOTSPOT_PASSWORD', '12345678')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # 投票配置
    VOTE_LIMIT_PER_IP = 1  # 每个IP最多投票次数
    VOTE_SESSION_TIMEOUT = 86400  # 投票会话超时时间（秒）
    
    # 抽奖配置
    LOTTERY_ANIMATION_DURATION = 5  # 抽奖动画持续时间（秒）
    
    # 管理员账号配置
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PHOTO_FOLDER, exist_ok=True)
        os.makedirs(Config.FILE_FOLDER, exist_ok=True)
        os.makedirs(BASE_DIR / 'database', exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
