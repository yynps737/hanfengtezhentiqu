"""
模型操作路由
"""
from flask import Blueprint
from api.services import SessionService
from api.utils import success_response, error_response

bp = Blueprint('model', __name__, url_prefix='/api')


@bp.route('/clear', methods=['POST'])
def clear_session():
    """
    清除当前会话数据
    
    Returns:
        JSON: 操作结果
    """
    try:
        SessionService.clear_model()
        return success_response(message='会话已清除')
    
    except Exception as e:
        return error_response(f'清除会话失败: {str(e)}', 500)


@bp.route('/model/info', methods=['GET'])
def get_model_info():
    """
    获取当前模型信息
    
    Returns:
        JSON: 模型信息（文件名、是否有模型等）
    """
    try:
        model = SessionService.get_model()
        has_model = SessionService.has_model()
        
        return success_response(
            data={
                'has_model': has_model,
                'filename': model['filename'] if has_model else None
            },
            message='获取模型信息成功'
        )
    
    except Exception as e:
        return error_response(f'获取模型信息失败: {str(e)}', 500)

