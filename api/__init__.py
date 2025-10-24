"""
Flask 应用工厂
"""
from flask import Flask
from api.config import Config
from api.routes import register_routes
from api.middleware import register_error_handlers, setup_cors


def create_app(config_class=Config):
    """
    创建 Flask 应用
    
    Args:
        config_class: 配置类（默认使用 Config）
        
    Returns:
        Flask: Flask 应用实例
    """
    # 创建 Flask 应用
    app = Flask(__name__,
                static_folder='../web/static',
                template_folder='../web')
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 设置 CORS
    setup_cors(app)
    
    # 注册路由
    register_routes(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    return app

