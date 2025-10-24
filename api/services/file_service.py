"""
文件处理服务
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app


class FileService:
    """文件处理服务"""
    
    @staticmethod
    def save_upload(file):
        """
        保存上传的文件到临时目录
        
        Args:
            file: Flask 文件对象
            
        Returns:
            str: 保存后的文件路径
        """
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath
    
    @staticmethod
    def delete_file(filepath):
        """
        删除文件
        
        Args:
            filepath: 文件路径
        """
        if os.path.exists(filepath):
            os.remove(filepath)
    
    @staticmethod
    def get_file_extension(filename):
        """
        获取文件扩展名
        
        Args:
            filename: 文件名
            
        Returns:
            str: 扩展名（小写）
        """
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

