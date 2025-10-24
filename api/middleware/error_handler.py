"""
统一错误处理中间件
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """
    注册全局错误处理器
    
    Args:
        app: Flask 应用实例
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理 400 错误"""
        return jsonify({
            'success': False,
            'error': '请求参数错误',
            'detail': str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """处理 404 错误"""
        return jsonify({
            'success': False,
            'error': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """处理 413 错误（文件过大）"""
        return jsonify({
            'success': False,
            'error': '上传文件过大，请上传小于 100MB 的文件'
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理 500 错误"""
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'detail': str(error)
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """处理所有 HTTP 异常"""
        return jsonify({
            'success': False,
            'error': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有未捕获的异常"""
        # 记录错误日志
        app.logger.error(f'未处理的异常: {str(error)}', exc_info=True)
        
        return jsonify({
            'success': False,
            'error': '服务器处理请求时发生错误',
            'detail': str(error)
        }), 500

