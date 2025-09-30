"""
Flask API - 极简版
只提供核心功能：STEP文件上传和网格数据转换
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step_loader import StepLoader
from core.mesh_converter import MeshConverter

# 创建Flask应用
app = Flask(__name__,
            static_folder='../web/static',
            template_folder='../web')

# 启用CORS
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大100MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'step', 'stp'}

# 全局变量存储当前模型
current_model = {
    'shape': None,
    'mesh': None,
    'filename': None
}


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return send_from_directory('../web', 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'message': 'CAD模型查看器运行正常'
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    上传STEP文件并转换为网格数据

    返回:
        JSON响应包含网格数据用于Three.js渲染
    """
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '文件格式不支持，请上传STEP或STP文件'}), 400

    try:
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 加载STEP文件
        loader = StepLoader()
        shape = loader.load_file(filepath)

        # 生成网格数据
        mesh_data = MeshConverter.shape_to_mesh(shape)

        # 保存到全局变量
        current_model['shape'] = shape
        current_model['mesh'] = mesh_data
        current_model['filename'] = filename

        # 清理临时文件
        os.remove(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'STEP文件上传成功',
            'mesh': mesh_data
        })

    except Exception as e:
        return jsonify({
            'error': f'文件处理失败: {str(e)}'
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """清除当前会话数据"""
    current_model['shape'] = None
    current_model['mesh'] = None
    current_model['filename'] = None

    return jsonify({
        'success': True,
        'message': '会话已清除'
    })


@app.errorhandler(413)
def too_large(e):
    """处理文件过大错误"""
    return jsonify({'error': '文件过大，最大支持100MB'}), 413


@app.errorhandler(500)
def server_error(e):
    """处理服务器错误"""
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 开发模式运行
    app.run(debug=True, host='0.0.0.0', port=5000)