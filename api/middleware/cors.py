"""
CORS 配置中间件
"""
from flask_cors import CORS


def setup_cors(app):
    """
    配置 CORS
    
    Args:
        app: Flask 应用实例
    """
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # 生产环境应该限制具体域名
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

