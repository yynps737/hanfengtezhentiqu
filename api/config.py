"""
应用配置
"""
import os
import tempfile


class Config:
    """基础配置"""
    # 文件上传配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = tempfile.gettempdir()
    ALLOWED_EXTENSIONS = {'step', 'stp'}
    
    # 网格转换配置
    LINEAR_DEFLECTION = 0.5
    ANGULAR_DEFLECTION = 0.5
    
    # 会话配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SESSION_TYPE = 'filesystem'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境应该从环境变量读取敏感配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 生产环境限制为 50MB

