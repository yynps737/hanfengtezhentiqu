"""
模型管理服务

架构说明：
- 使用 GeometryExtractor 提取完整几何和拓扑数据
- 保持精确几何类型和参数（不破坏数据结构）
- 支持焊缝识别所需的拓扑关系
- 前端自行决定如何渲染（不再提供网格转换）
"""
from core import StepLoader, GeometryExtractor
import os


class ModelService:
    """模型管理服务"""
    
    @staticmethod
    def load_step_file(filepath):
        """
        加载 STEP 文件
        
        Args:
            filepath: STEP 文件路径
            
        Returns:
            TopoDS_Shape: OpenCascade 形状对象
        """
        loader = StepLoader()
        shape = loader.load_file(filepath)
        return shape
    
    @staticmethod
    def extract_geometry(shape, filename=None):
        """
        提取完整的几何和拓扑数据（新架构）
        
        Args:
            shape: TopoDS_Shape 对象
            filename: 源文件名（可选）
            
        Returns:
            dict: 完整的几何数据，包含：
                - model: {vertices, edges, faces, topology}
                - features: {potential_weld_seams}
        """
        extractor = GeometryExtractor(shape, filename)
        geometry_data = extractor.extract_all()
        
        # 返回映射字典（用于后续操作）
        return {
            'geometry_data': geometry_data,
            'vertices_map': extractor.get_vertices_map(),
            'edges_map': extractor.get_edges_map(),
            'faces_map': extractor.get_faces_map()
        }
    
    @staticmethod
    def process_step_file(filepath):
        """
        处理 STEP 文件的完整流程
        
        Args:
            filepath: STEP 文件路径
            
        Returns:
            dict: 包含完整几何数据的字典
                {shape, geometry_data, vertices_map, edges_map, faces_map}
        """
        # 加载 STEP 文件
        shape = ModelService.load_step_file(filepath)
        filename = os.path.basename(filepath)
        
        # 提取完整几何和拓扑数据
        result = ModelService.extract_geometry(shape, filename)
        result['shape'] = shape
        
        return result

