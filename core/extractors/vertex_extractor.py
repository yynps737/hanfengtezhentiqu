"""
顶点提取器
从 TopoDS_Shape 提取所有顶点信息
"""

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_VERTEX
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from typing import List, Dict, Tuple


class VertexExtractor:
    """顶点提取器"""

    def __init__(self, shape):
        """
        初始化顶点提取器

        Args:
            shape: TopoDS_Shape 对象
        """
        if shape.IsNull():
            raise ValueError("输入形状为空")
        
        self.shape = shape
        self.vertices_data = []
        self.vertices_map = {}  # {hash: TopoDS_Vertex}
        self.vertex_id_map = {}  # {hash: id} 用于快速查找顶点ID
        
    def extract(self) -> Tuple[List[Dict], Dict]:
        """
        提取所有顶点信息

        Returns:
            tuple: (vertices_data, vertices_map)
                vertices_data: 顶点数据列表
                vertices_map: 哈希到顶点对象的映射
        """
        explorer = TopExp_Explorer(self.shape, TopAbs_VERTEX)
        vertex_id = 0
        
        while explorer.More():
            vertex = topods.Vertex(explorer.Current())
            
            # 获取顶点坐标
            point = BRep_Tool.Pnt(vertex)
            
            # 获取 OCC HashCode（永久标识符）
            # 使用 Python 内置 hash() 对 TShape 对象求哈希
            vertex_hash = hash(vertex.TShape())
            
            # 检查是否已经处理过这个顶点（去重）
            if vertex_hash not in self.vertex_id_map:
                vertex_data = {
                    'id': vertex_id,
                    'hash': vertex_hash,
                    'position': [point.X(), point.Y(), point.Z()]
                }
                
                self.vertices_data.append(vertex_data)
                self.vertices_map[vertex_hash] = vertex
                self.vertex_id_map[vertex_hash] = vertex_id
                
                vertex_id += 1
            
            explorer.Next()
        
        print(f"✓ 提取顶点: {len(self.vertices_data)} 个")
        return self.vertices_data, self.vertices_map
    
    def get_vertex_id_by_hash(self, vertex_hash: int) -> int:
        """
        根据哈希值获取顶点ID

        Args:
            vertex_hash: 顶点哈希值

        Returns:
            int: 顶点ID，如果不存在返回 -1
        """
        return self.vertex_id_map.get(vertex_hash, -1)
    
    def get_vertices_data(self) -> List[Dict]:
        """获取顶点数据列表"""
        return self.vertices_data
    
    def get_vertices_map(self) -> Dict:
        """获取顶点映射字典"""
        return self.vertices_map

