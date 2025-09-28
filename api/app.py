"""
Flask API 主应用
提供REST API接口用于焊缝检测
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import shutil

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step_loader import StepLoader
from core.weld_detector import WeldDetector
from core.mesh_converter import MeshConverter

# 创建Flask应用
app = Flask(__name__,
            static_folder='../web/static',
            template_folder='../web/templates')

# 启用CORS（跨域支持）
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大100MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'step', 'stp'}

# 全局变量存储当前分析结果（生产环境应使用数据库）
current_analysis = {
    'shape': None,
    'welds': [],
    'filename': None
}


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页 - 提供静态HTML"""
    return send_from_directory('../web', 'index.html')


@app.route('/fullscreen.html')
def fullscreen():
    """全屏视图页面"""
    return send_from_directory('../web', 'fullscreen.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '焊缝检测API运行正常'
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    上传STEP文件接口

    Returns:
        JSON响应包含上传状态
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

        # 保存到全局变量
        current_analysis['shape'] = shape
        current_analysis['filename'] = filename
        current_analysis['welds'] = []

        # 生成网格数据
        try:
            mesh_data = MeshConverter.shape_to_mesh(shape)
            current_analysis['mesh'] = mesh_data
        except Exception as e:
            print(f"网格生成失败: {e}")
            current_analysis['mesh'] = None

        # 清理临时文件
        os.remove(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'STEP文件上传成功',
            'mesh': current_analysis['mesh']  # 返回网格数据
        })

    except Exception as e:
        return jsonify({
            'error': f'文件处理失败: {str(e)}'
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    分析当前加载的模型，检测焊缝

    Request Body:
        {
            "parameters": {
                "fillet": {"min_angle": 60, "max_angle": 120},
                ...
            }
        }

    Returns:
        JSON响应包含检测到的焊缝
    """
    if current_analysis['shape'] is None:
        return jsonify({'error': '请先上传STEP文件'}), 400

    try:
        # 创建检测器
        detector = WeldDetector()

        # 更新参数（如果提供）
        if request.json and 'parameters' in request.json:
            detector.update_parameters(request.json['parameters'])

        # 执行检测
        shape = current_analysis['shape']
        welds = detector.detect_welds(shape)

        # 转换为JSON格式
        weld_data = detector.export_results()

        # 保存结果
        current_analysis['welds'] = weld_data

        # 统计信息
        summary = {
            'total': len(weld_data),
            'by_type': {}
        }
        for weld in weld_data:
            weld_type = weld['type']
            summary['by_type'][weld_type] = summary['by_type'].get(weld_type, 0) + 1

        return jsonify({
            'success': True,
            'filename': current_analysis['filename'],
            'welds': weld_data,
            'summary': summary
        })

    except Exception as e:
        return jsonify({
            'error': f'分析失败: {str(e)}'
        }), 500


@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    """获取当前检测参数"""
    detector = WeldDetector()
    return jsonify(detector.get_parameters())


@app.route('/api/parameters', methods=['POST'])
def update_parameters():
    """
    更新检测参数

    Request Body:
        {
            "fillet": {"min_angle": 60, "max_angle": 120},
            ...
        }
    """
    if not request.json:
        return jsonify({'error': '无效的请求数据'}), 400

    try:
        # 这里只是返回确认，实际参数会在analyze时应用
        return jsonify({
            'success': True,
            'message': '参数更新成功',
            'parameters': request.json
        })
    except Exception as e:
        return jsonify({
            'error': f'参数更新失败: {str(e)}'
        }), 500


@app.route('/api/export', methods=['GET'])
def export_results():
    """
    导出当前分析结果

    Query Parameters:
        format: json/csv (默认json)
    """
    if not current_analysis['welds']:
        return jsonify({'error': '无分析结果可导出'}), 400

    format_type = request.args.get('format', 'json')

    if format_type == 'json':
        return jsonify({
            'filename': current_analysis['filename'],
            'welds': current_analysis['welds']
        })

    elif format_type == 'csv':
        # CSV格式导出
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 写入头部
        writer.writerow([
            'Type', 'Angle(°)', 'Length(mm)',
            'Position_X', 'Position_Y', 'Position_Z',
            'Confidence'
        ])

        # 写入数据
        for weld in current_analysis['welds']:
            writer.writerow([
                weld['type'],
                weld['angle'],
                weld['length'],
                weld['position'][0],
                weld['position'][1],
                weld['position'][2],
                weld['confidence']
            ])

        # 返回CSV
        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=welds_{current_analysis["filename"]}.csv'
            }
        )

    else:
        return jsonify({'error': '不支持的导出格式'}), 400


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """清除当前会话数据"""
    current_analysis['shape'] = None
    current_analysis['welds'] = []
    current_analysis['filename'] = None

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