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
from core.topology_analyzer import TopologyAnalyzer
from core.geometry_calculator import GeometryCalculator
from core.mesh_converter import MeshConverter
from core.edge_analyzer import EdgeAnalyzer
from module.corner_joint_template import CornerJointTemplate, CornerJointParameters

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
    'filename': None,
    'topology_analyzer': None,  # 拓扑分析器，避免重复构建
    'edge_analyzer': None,
    'selected_edges': []
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
        current_analysis['topology_analyzer'] = None  # 延迟创建
        current_analysis['edge_analyzer'] = None  # 延迟创建，只在需要时创建
        current_analysis['selected_edges'] = []

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
    分析当前加载的模型，检测角接头

    Request Body:
        {
            "parameters": {
                "min_angle": 60,
                "max_angle": 120,
                "min_weld_length": 10
            }
        }

    Returns:
        JSON响应包含检测到的焊缝
    """
    if current_analysis['shape'] is None:
        return jsonify({'error': '请先上传STEP文件'}), 400

    try:
        # 创建分析器
        shape = current_analysis['shape']

        # 重用或创建拓扑分析器
        if not current_analysis['topology_analyzer']:
            current_analysis['topology_analyzer'] = TopologyAnalyzer(shape)
        topology_analyzer = current_analysis['topology_analyzer']

        geometry_calc = GeometryCalculator()

        # 创建角接头模板
        params = CornerJointParameters()

        # 更新参数（如果提供）
        if request.json and 'parameters' in request.json:
            req_params = request.json['parameters']
            if 'min_angle' in req_params:
                params.min_angle = req_params['min_angle']
            if 'max_angle' in req_params:
                params.max_angle = req_params['max_angle']
            if 'min_joint_length' in req_params:
                params.min_joint_length = req_params['min_joint_length']

        corner_template = CornerJointTemplate(params)

        # 执行检测
        joints = corner_template.analyze_shape(shape, topology_analyzer, geometry_calc)

        # 转换为JSON格式
        joint_data = []
        for joint in joints:
            joint_data.append({
                'type': 'corner',
                'subtype': joint.joint_type.value,
                'id': joint.joint_id,
                'angle': round(joint.joint_angle, 2),
                'length': round(joint.joint_length, 2),
                'plate1_thickness': round(joint.plate1_thickness, 2),
                'plate2_thickness': round(joint.plate2_thickness, 2),
                'position': list(joint.mid_point),
                'confidence': round(joint.confidence, 3),
                'quality_score': round(joint.quality_score, 1)
            })

        # 保存结果
        current_analysis['welds'] = joint_data

        # 获取统计信息
        stats = corner_template.get_statistics()

        return jsonify({
            'success': True,
            'filename': current_analysis['filename'],
            'welds': joint_data,
            'summary': stats
        })

    except Exception as e:
        return jsonify({
            'error': f'分析失败: {str(e)}'
        }), 500


@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    """获取当前检测参数"""
    params = CornerJointParameters()
    return jsonify({
        'min_angle': params.min_angle,
        'max_angle': params.max_angle,
        'min_joint_length': params.min_joint_length,
        'optimal_angle': params.optimal_angle,
        'edge_distance_threshold': params.edge_distance_threshold,
        'min_plate_thickness': params.min_plate_thickness,
        'max_plate_thickness': params.max_plate_thickness
    })


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
    current_analysis['topology_analyzer'] = None
    current_analysis['edge_analyzer'] = None
    current_analysis['selected_edges'] = []

    return jsonify({
        'success': True,
        'message': '会话已清除'
    })


@app.route('/api/edges/list', methods=['GET'])
def get_edges_list():
    """获取所有边的列表"""
    if not current_analysis['shape']:
        return jsonify({'error': '请先上传STEP文件'}), 400

    try:
        # 延迟创建拓扑分析器和边分析器
        if not current_analysis['topology_analyzer']:
            print("初始化拓扑分析器...")
            current_analysis['topology_analyzer'] = TopologyAnalyzer(current_analysis['shape'])
            print("拓扑分析器初始化完成")

        if not current_analysis['edge_analyzer']:
            print("初始化边分析器...")
            # 传递已有的拓扑分析器，避免重复构建
            current_analysis['edge_analyzer'] = EdgeAnalyzer(
                current_analysis['shape'],
                current_analysis['topology_analyzer']
            )
            print("边分析器初始化完成")

        edges_list = current_analysis['edge_analyzer'].get_all_edges_list()
        return jsonify({
            'success': True,
            'edges': edges_list,
            'total': len(edges_list)
        })

    except Exception as e:
        print(f"边分析器错误: {e}")
        return jsonify({
            'error': f'获取边列表失败: {str(e)}'
        }), 500


@app.route('/api/edges/analyze', methods=['POST'])
def analyze_edges():
    """
    深度分析选中的边

    Request Body:
        {
            "edge_ids": ["EDGE_0", "EDGE_1", ...]
        }
    """
    if not current_analysis['shape']:
        return jsonify({'error': '请先上传STEP文件'}), 400

    # 确保拓扑分析器和边分析器已创建
    if not current_analysis['topology_analyzer']:
        current_analysis['topology_analyzer'] = TopologyAnalyzer(current_analysis['shape'])

    if not current_analysis['edge_analyzer']:
        current_analysis['edge_analyzer'] = EdgeAnalyzer(
            current_analysis['shape'],
            current_analysis['topology_analyzer']
        )

    try:
        edge_ids = request.json.get('edge_ids', [])

        if not edge_ids:
            return jsonify({'error': '请选择要分析的边'}), 400

        # 保存选中的边
        current_analysis['selected_edges'] = edge_ids

        # 分析边
        analyzer = current_analysis['edge_analyzer']
        analysis_results = analyzer.analyze_multiple_edges(edge_ids)

        return jsonify({
            'success': True,
            'analysis': analysis_results,
            'count': len(analysis_results)
        })

    except Exception as e:
        return jsonify({
            'error': f'边分析失败: {str(e)}'
        }), 500


@app.route('/api/edges/analyze/<edge_id>', methods=['GET'])
def analyze_single_edge(edge_id):
    """分析单条边"""
    if not current_analysis['shape']:
        return jsonify({'error': '请先上传STEP文件'}), 400

    # 确保拓扑分析器和边分析器已创建
    if not current_analysis['topology_analyzer']:
        current_analysis['topology_analyzer'] = TopologyAnalyzer(current_analysis['shape'])

    if not current_analysis['edge_analyzer']:
        current_analysis['edge_analyzer'] = EdgeAnalyzer(
            current_analysis['shape'],
            current_analysis['topology_analyzer']
        )

    try:
        analyzer = current_analysis['edge_analyzer']
        analysis = analyzer.analyze_edge(edge_id)

        if 'error' in analysis:
            return jsonify({'error': analysis['error']}), 404

        return jsonify({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        return jsonify({
            'error': f'边分析失败: {str(e)}'
        }), 500


@app.route('/api/edges/export', methods=['POST'])
def export_edge_analysis():
    """
    导出边分析结果

    Request Body:
        {
            "format": "json" | "txt",
            "edge_ids": ["EDGE_0", "EDGE_1", ...]
        }
    """
    if not current_analysis['shape']:
        return jsonify({'error': '请先上传STEP文件'}), 400

    # 确保拓扑分析器和边分析器已创建
    if not current_analysis['topology_analyzer']:
        current_analysis['topology_analyzer'] = TopologyAnalyzer(current_analysis['shape'])

    if not current_analysis['edge_analyzer']:
        current_analysis['edge_analyzer'] = EdgeAnalyzer(
            current_analysis['shape'],
            current_analysis['topology_analyzer']
        )

    try:
        format_type = request.json.get('format', 'json')
        edge_ids = request.json.get('edge_ids', current_analysis['selected_edges'])

        if not edge_ids:
            return jsonify({'error': '没有选中的边'}), 400

        # 分析边
        analyzer = current_analysis['edge_analyzer']
        analysis_results = analyzer.analyze_multiple_edges(edge_ids)

        if format_type == 'json':
            return jsonify({
                'filename': current_analysis['filename'],
                'edge_count': len(edge_ids),
                'edges': analysis_results
            })

        elif format_type == 'txt':
            # 生成文本格式
            import io

            output = io.StringIO()
            output.write(f"边特征深度分析报告\n")
            output.write(f"=" * 80 + "\n")
            output.write(f"文件: {current_analysis['filename']}\n")
            output.write(f"分析边数: {len(edge_ids)}\n")
            output.write(f"=" * 80 + "\n\n")

            for result in analysis_results:
                output.write(f"\n{'='*80}\n")
                output.write(f"边 {result['edge_id']}\n")
                output.write(f"{'='*80}\n\n")

                # 1. 几何信息
                output.write("【几何信息】\n")
                output.write("-" * 40 + "\n")
                geom = result['geometry']
                output.write(f"类型: {geom['type']}\n")
                output.write(f"类型代码: {geom.get('type_code', 'N/A')}\n")
                output.write(f"长度: {geom['length']:.6f} mm\n")
                output.write(f"是否闭合: {geom.get('is_closed', False)}\n")
                output.write(f"是否退化: {geom.get('is_degenerated', False)}\n")
                output.write(f"\n参数范围:\n")
                output.write(f"  起始: {geom['parameter_range']['first']:.6f}\n")
                output.write(f"  结束: {geom['parameter_range']['last']:.6f}\n")
                output.write(f"\n坐标点:\n")
                output.write(f"  起点: [{', '.join(f'{x:.6f}' for x in geom['points']['start'])}]\n")
                output.write(f"  中点: [{', '.join(f'{x:.6f}' for x in geom['points']['middle'])}]\n")
                output.write(f"  终点: [{', '.join(f'{x:.6f}' for x in geom['points']['end'])}]\n")

                # 曲率信息
                if geom.get('curvature') is not None:
                    output.write(f"曲率: {geom['curvature']:.6f}\n")

                # 特定几何信息（直线、圆等）
                if 'line_info' in geom:
                    output.write(f"\n直线信息:\n")
                    output.write(f"  原点: {geom['line_info']['origin']}\n")
                    output.write(f"  方向: {geom['line_info']['direction']}\n")
                if 'circle_info' in geom:
                    output.write(f"\n圆信息:\n")
                    output.write(f"  圆心: {geom['circle_info']['center']}\n")
                    output.write(f"  半径: {geom['circle_info']['radius']:.6f}\n")
                    output.write(f"  轴向: {geom['circle_info']['axis']}\n")

                # 2. 拓扑信息
                output.write(f"\n【拓扑信息】\n")
                output.write("-" * 40 + "\n")
                topo = result['topology']
                output.write(f"邻接面数: {topo['adjacent_face_count']}\n")
                output.write(f"方向: {topo['orientation']}\n")
                output.write(f"是否缝合边: {topo['is_seam']}\n")
                output.write(f"是否流形: {topo['is_manifold']}\n")

                # 3. 顶点信息
                output.write(f"\n【顶点信息】\n")
                output.write("-" * 40 + "\n")
                verts = result['vertices']
                output.write(f"顶点数: {verts['count']}\n")
                output.write(f"是否闭合: {verts['is_closed']}\n")
                if verts['start']:
                    output.write(f"起始顶点:\n")
                    output.write(f"  坐标: [{', '.join(f'{x:.6f}' for x in verts['start']['coordinates'])}]\n")
                    output.write(f"  容差: {verts['start']['tolerance']:.3e}\n")
                if verts['end'] and verts['end'] != verts['start']:
                    output.write(f"结束顶点:\n")
                    output.write(f"  坐标: [{', '.join(f'{x:.6f}' for x in verts['end']['coordinates'])}]\n")
                    output.write(f"  容差: {verts['end']['tolerance']:.3e}\n")

                # 4. 邻接面信息
                output.write(f"\n【邻接面详细信息】\n")
                output.write("-" * 40 + "\n")
                for i, face in enumerate(result['adjacent_faces']):
                    output.write(f"\n面 {i+1}:\n")
                    face_geom = face['geometry']
                    output.write(f"  类型: {face_geom['type']}\n")
                    output.write(f"  面积: {face_geom['area']:.6f} mm²\n")
                    output.write(f"  质心: [{', '.join(f'{x:.6f}' for x in face_geom['centroid'])}]\n")
                    if face_geom.get('normal_at_center'):
                        output.write(f"  法向量: [{', '.join(f'{x:.6f}' for x in face_geom['normal_at_center'])}]\n")
                    output.write(f"  UV参数范围:\n")
                    output.write(f"    U: [{face_geom['uv_range']['u_min']:.6f}, {face_geom['uv_range']['u_max']:.6f}]\n")
                    output.write(f"    V: [{face_geom['uv_range']['v_min']:.6f}, {face_geom['uv_range']['v_max']:.6f}]\n")

                    # 面的特定信息
                    if 'plane_info' in face_geom:
                        output.write(f"  平面信息:\n")
                        output.write(f"    原点: {face_geom['plane_info']['origin']}\n")
                        output.write(f"    法向: {face_geom['plane_info']['normal']}\n")
                    if 'cylinder_info' in face_geom:
                        output.write(f"  圆柱面信息:\n")
                        output.write(f"    中心: {face_geom['cylinder_info']['center']}\n")
                        output.write(f"    半径: {face_geom['cylinder_info']['radius']:.6f}\n")
                        output.write(f"    轴向: {face_geom['cylinder_info']['axis']}\n")

                    # 面的属性
                    face_props = face['properties']
                    output.write(f"  边界框对角线: {face_props['bounding_box']['diagonal']:.6f} mm\n")
                    output.write(f"  边数: {face_props['edge_count']}\n")
                    output.write(f"  顶点数: {face_props['vertex_count']}\n")

                # 5. 物理属性
                output.write(f"\n【物理属性】\n")
                output.write("-" * 40 + "\n")
                props = result['properties']
                output.write(f"容差: {props['tolerance']:.3e}\n")
                output.write(f"线性质量: {props['linear_mass']:.6f}\n")
                if 'centroid' in props:
                    output.write(f"质心: [{', '.join(f'{x:.6f}' for x in props['centroid'])}]\n")
                output.write(f"边界框:\n")
                output.write(f"  最小: [{', '.join(f'{x:.6f}' for x in props['bounding_box']['min'])}]\n")
                output.write(f"  最大: [{', '.join(f'{x:.6f}' for x in props['bounding_box']['max'])}]\n")
                output.write(f"  对角线: {props['bounding_box']['diagonal']:.6f} mm\n")

                # 6. 参数信息
                output.write(f"\n【参数信息】\n")
                output.write("-" * 40 + "\n")
                param = result['parametric']
                if 'sample_points' in param:
                    output.write(f"采样点数: {len(param['sample_points'])}\n")
                    # 只显示前3个和后3个采样点
                    for i in [0, 1, 2, -3, -2, -1]:
                        if 0 <= i < len(param['sample_points']) or i < 0:
                            pt = param['sample_points'][i]
                            output.write(f"  采样点[{i if i >= 0 else len(param['sample_points']) + i}]: ")
                            output.write(f"t={pt['parameter']:.6f}, ")
                            output.write(f"坐标=[{', '.join(f'{x:.3f}' for x in pt['point'])}]\n")

                if param.get('derivatives_at_midpoint'):
                    derivs = param['derivatives_at_midpoint']
                    output.write(f"\n中点导数:\n")
                    output.write(f"  一阶导数: [{', '.join(f'{x:.6f}' for x in derivs['first_derivative'])}]\n")
                    output.write(f"  二阶导数: [{', '.join(f'{x:.6f}' for x in derivs['second_derivative'])}]\n")
                    output.write(f"  切向量模: {derivs['tangent_magnitude']:.6f}\n")

                # 7. 质量评估
                output.write(f"\n【质量评估】\n")
                output.write("-" * 40 + "\n")
                quality = result['quality']
                output.write(f"是否为小边: {quality['is_small_edge']}\n")
                output.write(f"长度质量: {quality['length_quality']}\n")
                if quality.get('curvature_variation'):
                    curv_var = quality['curvature_variation']
                    output.write(f"曲率变化:\n")
                    output.write(f"  最小: {curv_var['min']:.6f}\n")
                    output.write(f"  最大: {curv_var['max']:.6f}\n")
                    output.write(f"  平均: {curv_var['mean']:.6f}\n")
                    output.write(f"  标准差: {curv_var['std']:.6f}\n")

                output.write("\n")

            # 返回文本文件
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/plain',
                headers={
                    'Content-Disposition': f'attachment;filename=edge_analysis_{current_analysis["filename"]}.txt'
                }
            )

        else:
            return jsonify({'error': '不支持的导出格式'}), 400

    except Exception as e:
        return jsonify({
            'error': f'导出失败: {str(e)}'
        }), 500


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