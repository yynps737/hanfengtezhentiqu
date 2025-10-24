"""
邻接关系构建器
构建面-边-顶点之间的拓扑邻接关系

关键用途：
1. edge_face_map: 用于焊缝识别（找到边的相邻面）
2. face_adjacency: 用于分析面之间的连接关系
3. vertex_edge_map: 用于分析顶点周围的边
"""

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.TopoDS import topods
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_ListIteratorOfListOfShape
from OCC.Core.TopExp import topexp
from typing import Dict, List, Set
from collections import defaultdict


class AdjacencyBuilder:
    """拓扑邻接关系构建器"""

    def __init__(self, shape, faces_data: List[Dict], edges_data: List[Dict], vertices_data: List[Dict]):
        """
        初始化邻接关系构建器

        Args:
            shape: TopoDS_Shape 对象
            faces_data: 面数据列表（来自FaceExtractor）
            edges_data: 边数据列表（来自EdgeExtractor）
            vertices_data: 顶点数据列表（来自VertexExtractor）
        """
        if shape.IsNull():
            raise ValueError("输入形状为空")
        
        self.shape = shape
        self.faces_data = faces_data
        self.edges_data = edges_data
        self.vertices_data = vertices_data
        
        # 构建哈希到ID的映射
        self.face_hash_to_id = {face['hash']: face['id'] for face in faces_data}
        self.edge_hash_to_id = {edge['hash']: edge['id'] for edge in edges_data}
        self.vertex_hash_to_id = {vertex['hash']: vertex['id'] for vertex in vertices_data}
        
        # 拓扑关系
        self.edge_face_map = {}  # {edge_id: [face_id, ...]}
        self.face_adjacency = {}  # {face_id: [adjacent_face_id, ...]}
        self.vertex_edge_map = {}  # {vertex_id: [edge_id, ...]}
        
    def build(self) -> Dict:
        """
        构建所有拓扑邻接关系

        Returns:
            dict: 包含所有拓扑关系的字典
        """
        # 1. 构建边-面映射（关键：用于焊缝识别）
        self._build_edge_face_map()
        
        # 2. 构建面邻接关系
        self._build_face_adjacency()
        
        # 3. 构建顶点-边映射
        self._build_vertex_edge_map()
        
        # 4. 更新边数据中的相邻面信息
        self._update_edges_adjacent_faces()
        
        print(f"✓ 构建拓扑关系:")
        print(f"  - 边-面映射: {len(self.edge_face_map)} 条边")
        print(f"  - 面邻接: {len(self.face_adjacency)} 个面")
        print(f"  - 顶点-边映射: {len(self.vertex_edge_map)} 个顶点")
        
        return {
            'edge_face_map': self.edge_face_map,
            'face_adjacency': self.face_adjacency,
            'vertex_edge_map': self.vertex_edge_map
        }
    
    def _build_edge_face_map(self):
        """
        构建边-面映射关系
        
        对于每条边，找出所有包含它的面
        """
        # 使用 OCC 的 TopExp 工具构建映射
        edge_face_map_occ = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(
            self.shape,
            TopAbs_EDGE,
            TopAbs_FACE,
            edge_face_map_occ
        )
        
        # 转换为我们的数据结构
        for i in range(1, edge_face_map_occ.Size() + 1):
            edge = edge_face_map_occ.FindKey(i)
            edge_hash = hash(edge.TShape())
            
            if edge_hash in self.edge_hash_to_id:
                edge_id = self.edge_hash_to_id[edge_hash]
                
                # 获取相邻的面
                face_list = edge_face_map_occ.FindFromIndex(i)
                adjacent_face_ids = []
                
                # 使用迭代器遍历列表
                face_iter = TopTools_ListIteratorOfListOfShape(face_list)
                while face_iter.More():
                    face = topods.Face(face_iter.Value())
                    face_hash = hash(face.TShape())
                    
                    if face_hash in self.face_hash_to_id:
                        face_id = self.face_hash_to_id[face_hash]
                        adjacent_face_ids.append(face_id)
                    
                    face_iter.Next()
                
                if adjacent_face_ids:
                    self.edge_face_map[edge_id] = adjacent_face_ids
    
    def _build_face_adjacency(self):
        """
        构建面邻接关系
        
        如果两个面共享一条边，则它们是邻接的
        """
        # 从边-面映射反向构建面邻接关系
        face_neighbors = defaultdict(set)
        
        for edge_id, face_ids in self.edge_face_map.items():
            # 如果一条边连接多个面，这些面互相邻接
            if len(face_ids) >= 2:
                for i, face_id1 in enumerate(face_ids):
                    for face_id2 in face_ids[i+1:]:
                        face_neighbors[face_id1].add(face_id2)
                        face_neighbors[face_id2].add(face_id1)
        
        # 转换为列表并排序
        for face_id, neighbors in face_neighbors.items():
            self.face_adjacency[face_id] = sorted(list(neighbors))
    
    def _build_vertex_edge_map(self):
        """
        构建顶点-边映射关系
        
        对于每个顶点，找出所有连接到它的边
        """
        # 使用边数据中的顶点信息构建
        vertex_edges = defaultdict(set)
        
        for edge in self.edges_data:
            edge_id = edge['id']
            vertices = edge.get('vertices', [])
            
            for vertex_id in vertices:
                vertex_edges[vertex_id].add(edge_id)
        
        # 转换为列表并排序
        for vertex_id, edges in vertex_edges.items():
            self.vertex_edge_map[vertex_id] = sorted(list(edges))
    
    def _update_edges_adjacent_faces(self):
        """
        更新边数据中的 adjacent_faces 字段
        """
        for edge in self.edges_data:
            edge_id = edge['id']
            if edge_id in self.edge_face_map:
                edge['adjacent_faces'] = self.edge_face_map[edge_id]
    
    def get_edge_adjacent_faces(self, edge_id: int) -> List[int]:
        """
        获取边的相邻面ID列表

        Args:
            edge_id: 边ID

        Returns:
            list: 相邻面ID列表
        """
        return self.edge_face_map.get(edge_id, [])
    
    def get_face_neighbors(self, face_id: int) -> List[int]:
        """
        获取面的邻接面ID列表

        Args:
            face_id: 面ID

        Returns:
            list: 邻接面ID列表
        """
        return self.face_adjacency.get(face_id, [])
    
    def get_vertex_edges(self, vertex_id: int) -> List[int]:
        """
        获取顶点连接的边ID列表

        Args:
            vertex_id: 顶点ID

        Returns:
            list: 边ID列表
        """
        return self.vertex_edge_map.get(vertex_id, [])
    
    def is_boundary_edge(self, edge_id: int) -> bool:
        """
        判断边是否为边界边（只连接一个面）

        Args:
            edge_id: 边ID

        Returns:
            bool: 是否为边界边
        """
        adjacent_faces = self.get_edge_adjacent_faces(edge_id)
        return len(adjacent_faces) == 1
    
    def is_internal_edge(self, edge_id: int) -> bool:
        """
        判断边是否为内部边（连接两个或更多面）

        Args:
            edge_id: 边ID

        Returns:
            bool: 是否为内部边
        """
        adjacent_faces = self.get_edge_adjacent_faces(edge_id)
        return len(adjacent_faces) >= 2
    
    def get_potential_weld_edges(self) -> List[int]:
        """
        获取潜在的焊缝边（连接恰好两个面的边）

        Returns:
            list: 边ID列表
        """
        potential_edges = []
        
        for edge_id, face_ids in self.edge_face_map.items():
            if len(face_ids) == 2:
                potential_edges.append(edge_id)
        
        return potential_edges
    
    def get_topology_summary(self) -> Dict:
        """
        获取拓扑关系摘要

        Returns:
            dict: 拓扑摘要信息
        """
        total_edges = len(self.edge_face_map)
        boundary_edges = sum(1 for edge_id in self.edge_face_map if self.is_boundary_edge(edge_id))
        internal_edges = sum(1 for edge_id in self.edge_face_map if self.is_internal_edge(edge_id))
        potential_weld_edges = len(self.get_potential_weld_edges())
        
        return {
            'total_edges': total_edges,
            'boundary_edges': boundary_edges,
            'internal_edges': internal_edges,
            'potential_weld_edges': potential_weld_edges,
            'total_faces': len(self.face_adjacency),
            'total_vertices': len(self.vertex_edge_map)
        }

