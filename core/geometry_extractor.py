"""
几何提取器 - 主入口类
整合所有提取器、拓扑分析和序列化功能
输出完整的几何和拓扑数据（保持CAD模型的精确性）
"""

from .extractors import VertexExtractor, EdgeExtractor, FaceExtractor
from .topology import AdjacencyBuilder
from .serializers import GeometrySerializer
from typing import Dict, Tuple


class GeometryExtractor:
    """
    几何提取器 - 主入口类
    
    职责：
    1. 从 TopoDS_Shape 提取完整的几何和拓扑信息
    2. 保持 OCC 的精确几何类型和参数
    3. 构建拓扑邻接关系（特别是边-面关系，用于焊缝识别）
    4. 序列化为 JSON 格式
    
    设计理念：
    - 保留完整的 CAD 几何数据（不转换为网格）
    - 前端根据需要自行决定渲染方式
    - 支持精确的焊缝识别和拓扑分析
    """

    def __init__(self, shape, filename: str = None):
        """
        初始化几何提取器

        Args:
            shape: TopoDS_Shape 对象
            filename: 源文件名（可选）
        """
        if shape.IsNull():
            raise ValueError("输入形状为空")
        
        self.shape = shape
        self.filename = filename
        
        # 提取器
        self.vertex_extractor = None
        self.edge_extractor = None
        self.face_extractor = None
        
        # 提取的数据
        self.vertices_data = []
        self.edges_data = []
        self.faces_data = []
        self.topology = {}
        
        # 映射（用于回溯 OCC 对象）
        self.vertices_map = {}
        self.edges_map = {}
        self.faces_map = {}
        
    def extract_all(self) -> Dict:
        """
        提取所有几何和拓扑信息

        Returns:
            dict: 完整的几何数据（符合 geometry_data_schema.md）
        """
        print("=" * 60)
        print("开始提取几何和拓扑信息...")
        print("=" * 60)
        
        # 步骤1: 提取顶点
        print("\n[1/5] 提取顶点...")
        self.vertex_extractor = VertexExtractor(self.shape)
        self.vertices_data, self.vertices_map = self.vertex_extractor.extract()
        
        # 步骤2: 提取边
        print("\n[2/5] 提取边...")
        self.edge_extractor = EdgeExtractor(self.shape, self.vertex_extractor)
        self.edges_data, self.edges_map = self.edge_extractor.extract()
        
        # 步骤3: 提取面
        print("\n[3/5] 提取面...")
        self.face_extractor = FaceExtractor(self.shape, self.edge_extractor)
        self.faces_data, self.faces_map = self.face_extractor.extract()
        
        # 步骤4: 构建拓扑关系
        print("\n[4/5] 构建拓扑关系...")
        adjacency_builder = AdjacencyBuilder(
            self.shape,
            self.faces_data,
            self.edges_data,
            self.vertices_data
        )
        self.topology = adjacency_builder.build()
        
        # 步骤5: 序列化
        print("\n[5/5] 序列化数据...")
        serializer = GeometrySerializer(
            self.shape,
            self.vertices_data,
            self.edges_data,
            self.faces_data,
            self.topology,
            self.filename
        )
        result = serializer.serialize()
        
        print("\n" + "=" * 60)
        print("提取完成！")
        print("=" * 60)
        
        return result
    
    def get_vertices_map(self) -> Dict:
        """
        获取顶点映射（hash -> TopoDS_Vertex）
        
        Returns:
            dict: 顶点映射
        """
        return self.vertices_map
    
    def get_edges_map(self) -> Dict:
        """
        获取边映射（hash -> TopoDS_Edge）
        
        用途：焊缝选择时，前端传递 edge_hash，后端通过此映射回溯到 OCC 对象
        
        Returns:
            dict: 边映射
        """
        return self.edges_map
    
    def get_faces_map(self) -> Dict:
        """
        获取面映射（hash -> TopoDS_Face）
        
        Returns:
            dict: 面映射
        """
        return self.faces_map
    
    def get_edge_by_hash(self, edge_hash: int):
        """
        根据哈希值获取边对象

        Args:
            edge_hash: 边哈希值

        Returns:
            TopoDS_Edge: 边对象，如果不存在返回 None
        """
        return self.edges_map.get(edge_hash)
    
    def get_face_by_hash(self, face_hash: int):
        """
        根据哈希值获取面对象

        Args:
            face_hash: 面哈希值

        Returns:
            TopoDS_Face: 面对象，如果不存在返回 None
        """
        return self.faces_map.get(face_hash)
    
    def get_topology_summary(self) -> Dict:
        """
        获取拓扑摘要信息

        Returns:
            dict: 拓扑摘要
        """
        edge_face_map = self.topology.get('edge_face_map', {})
        potential_weld_edges = [
            edge_id for edge_id, faces in edge_face_map.items() 
            if len(faces) == 2
        ]
        
        return {
            'num_vertices': len(self.vertices_data),
            'num_edges': len(self.edges_data),
            'num_faces': len(self.faces_data),
            'num_potential_weld_edges': len(potential_weld_edges),
            'has_topology': bool(self.topology)
        }


# 兼容性：保留原有的 extract_edges 方法
def extract_edges_legacy(shape):
    """
    提取边信息（兼容旧版 API）
    
    注意：这是为了兼容现有代码，建议使用 GeometryExtractor.extract_all()
    
    Args:
        shape: TopoDS_Shape 对象
    
    Returns:
        tuple: (edges_data, edges_map)
    """
    print("警告: 使用的是遗留 API，建议升级到 GeometryExtractor.extract_all()")
    
    extractor = GeometryExtractor(shape)
    vertex_extractor = VertexExtractor(shape)
    vertex_extractor.extract()
    
    edge_extractor = EdgeExtractor(shape, vertex_extractor)
    edges_data, edges_map = edge_extractor.extract()
    
    return edges_data, edges_map

