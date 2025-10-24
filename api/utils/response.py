"""
统一响应格式工具
"""
from flask import jsonify


def success_response(data=None, message='操作成功', **kwargs):
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        **kwargs: 其他额外字段
        
    Returns:
        Response: Flask JSON 响应
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    # 添加额外字段
    response.update(kwargs)
    
    return jsonify(response)


def error_response(message='操作失败', status_code=400, **kwargs):
    """
    错误响应
    
    Args:
        message: 错误消息
        status_code: HTTP 状态码
        **kwargs: 其他额外字段
        
    Returns:
        tuple: (Response, status_code)
    """
    response = {
        'success': False,
        'error': message
    }
    
    # 添加额外字段
    response.update(kwargs)
    
    return jsonify(response), status_code

