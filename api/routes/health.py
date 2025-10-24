"""
健康检查路由
"""
from flask import Blueprint
from api.utils import success_response

bp = Blueprint('health', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    
    Returns:
        JSON: 服务状态信息
    """
    return success_response(
        data={'status': 'healthy'},
        message='CAD模型查看器运行正常'
    )

