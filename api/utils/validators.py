"""
验证器工具
"""
from flask import current_app


def allowed_file(filename):
    """
    检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否允许
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def validate_file(request):
    """
    验证上传的文件
    
    Args:
        request: Flask request 对象
        
    Returns:
        str or None: 错误信息，如果验证通过则返回 None
    """
    # 检查是否有文件
    if 'file' not in request.files:
        return '未找到文件'
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return '未选择文件'
    
    # 检查文件格式
    if not allowed_file(file.filename):
        return '文件格式不支持，请上传STEP或STP文件'
    
    return None

