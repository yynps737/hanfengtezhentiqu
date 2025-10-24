"""
路由模块
"""
from flask import send_from_directory


def register_routes(app):
    """
    注册所有路由
    
    Args:
        app: Flask 应用实例
    """
    
    # 主页路由
    @app.route('/')
    def index():
        """返回前端页面"""
        return send_from_directory('../web', 'index.html')
    
    # 注册蓝图
    from .health import bp as health_bp
    from .upload import bp as upload_bp
    from .model import bp as model_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(model_bp)

