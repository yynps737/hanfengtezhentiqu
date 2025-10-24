"""
文件上传路由
"""
from flask import Blueprint, request
from api.services import FileService, ModelService, SessionService
from api.utils import validate_file, success_response, error_response

bp = Blueprint('upload', __name__, url_prefix='/api')


@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传 STEP 文件并提取完整几何数据
    
    新架构流程:
        1. 验证文件
        2. 保存文件到临时目录
        3. 加载 STEP 文件
        4. 提取完整几何和拓扑数据（顶点、边、面、拓扑关系）
        5. （可选）生成网格用于预览
        6. 保存到会话
        7. 返回完整几何数据
    
    Returns:
        JSON: 包含完整几何数据的响应
            - model: {vertices, edges, faces, topology, metadata}
            - features: {potential_weld_seams}
            - mesh: (可选) 用于预览的三角网格
    """
    # 验证请求
    error = validate_file(request)
    if error:
        return error_response(error, 400)
    
    file = request.files['file']
    filepath = None
    
    try:
        # 保存文件
        filepath = FileService.save_upload(file)
        
        # 处理 STEP 文件（新架构）
        result = ModelService.process_step_file(filepath)
        
        # 保存到会话
        SessionService.save_model(
            shape=result['shape'],
            geometry_data=result['geometry_data'],
            edges_map=result['edges_map'],
            faces_map=result['faces_map'],
            vertices_map=result['vertices_map'],
            mesh=result.get('mesh'),  # 可选
            filename=file.filename
        )
        
        # 构建返回数据
        response_data = {
            'geometry': result['geometry_data']
        }
        
        # 如果生成了网格，也返回（用于兼容旧前端或快速预览）
        if 'mesh' in result:
            response_data['mesh'] = result['mesh']
        
        # 返回响应
        return success_response(
            message='STEP文件上传成功',
            filename=file.filename,
            **response_data
        )
        
    except FileNotFoundError as e:
        return error_response(f'文件不存在: {str(e)}', 404)
    
    except ValueError as e:
        return error_response(f'文件验证失败: {str(e)}', 400)
    
    except Exception as e:
        return error_response(f'文件处理失败: {str(e)}', 500)
    
    finally:
        # 清理临时文件
        if filepath:
            FileService.delete_file(filepath)

