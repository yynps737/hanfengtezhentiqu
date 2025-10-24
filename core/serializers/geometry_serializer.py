"""
几何序列化器
将提取的几何和拓扑数据序列化为 JSON 格式
同时计算模型的元数据（包围盒、统计信息等）
"""

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from typing import Dict, List
import datetime


class GeometrySerializer:
    """几何数据序列化器"""

    def __init__(
        self,
        shape,
        vertices_data: List[Dict],
        edges_data: List[Dict],
        faces_data: List[Dict],
        topology: Dict,
        filename: str = None
    ):
        """
        初始化序列化器

        Args:
            shape: TopoDS_Shape 对象
            vertices_data: 顶点数据列表
            edges_data: 边数据列表
            faces_data: 面数据列表
            topology: 拓扑关系字典
            filename: 源文件名
        """
        self.shape = shape
        self.vertices_data = vertices_data
        self.edges_data = edges_data
        self.faces_data = faces_data
        self.topology = topology
        self.filename = filename
        
    def serialize(self) -> Dict:
        """
        序列化为完整的 JSON 数据结构

        Returns:
            dict: 符合 geometry_data_schema.md 定义的完整数据结构
        """
        # 计算元数据
        metadata = self._build_metadata()
        
        # 构建模型数据
        model = {
            'metadata': metadata,
            'vertices': self.vertices_data,
            'edges': self.edges_data,
            'faces': self.faces_data,
            'topology': self.topology
        }
        
        # 构建特征数据（可选）
        features = self._build_features()
        
        # 构建完整数据
        data = {
            'model': model
        }
        
        if features:
            data['features'] = features
        
        print(f"✓ 序列化完成:")
        print(f"  - 顶点: {len(self.vertices_data)}")
        print(f"  - 边: {len(self.edges_data)}")
        print(f"  - 面: {len(self.faces_data)}")
        
        return data
    
    def _build_metadata(self) -> Dict:
        """
        构建模型元数据

        Returns:
            dict: 元数据
        """
        # 计算包围盒
        bounding_box = self._calculate_bounding_box()
        
        # 构建元数据
        metadata = {
            'filename': self.filename or 'unknown',
            'upload_time': datetime.datetime.now().isoformat(),
            'bounding_box': bounding_box,
            'statistics': {
                'num_vertices': len(self.vertices_data),
                'num_edges': len(self.edges_data),
                'num_faces': len(self.faces_data),
                'topology_summary': self._get_topology_summary()
            }
        }
        
        return metadata
    
    def _calculate_bounding_box(self) -> Dict:
        """
        计算模型的包围盒

        Returns:
            dict: 包围盒 {min: [x, y, z], max: [x, y, z]}
        """
        try:
            bbox = Bnd_Box()
            brepbndlib.Add(self.shape, bbox)
            
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            
            return {
                'min': [xmin, ymin, zmin],
                'max': [xmax, ymax, zmax],
                'center': [
                    (xmin + xmax) / 2,
                    (ymin + ymax) / 2,
                    (zmin + zmax) / 2
                ],
                'size': [
                    xmax - xmin,
                    ymax - ymin,
                    zmax - zmin
                ]
            }
        except Exception as e:
            print(f"警告: 计算包围盒失败: {e}")
            return {
                'min': [0, 0, 0],
                'max': [0, 0, 0],
                'center': [0, 0, 0],
                'size': [0, 0, 0]
            }
    
    def _get_topology_summary(self) -> Dict:
        """
        获取拓扑摘要信息

        Returns:
            dict: 拓扑摘要
        """
        edge_face_map = self.topology.get('edge_face_map', {})
        face_adjacency = self.topology.get('face_adjacency', {})
        
        # 统计不同类型的边
        boundary_edges = []
        internal_edges = []
        potential_weld_edges = []
        
        for edge_id, face_ids in edge_face_map.items():
            num_faces = len(face_ids)
            if num_faces == 1:
                boundary_edges.append(edge_id)
            elif num_faces == 2:
                internal_edges.append(edge_id)
                potential_weld_edges.append(edge_id)
            elif num_faces > 2:
                internal_edges.append(edge_id)
        
        return {
            'boundary_edges_count': len(boundary_edges),
            'internal_edges_count': len(internal_edges),
            'potential_weld_edges_count': len(potential_weld_edges),
            'connected_faces_count': len(face_adjacency)
        }
    
    def _build_features(self) -> Dict:
        """
        构建特征数据（可选）

        Returns:
            dict: 特征数据
        """
        # 提取潜在的焊缝边
        potential_weld_seams = self._extract_potential_weld_seams()
        
        if potential_weld_seams:
            return {
                'potential_weld_seams': potential_weld_seams
            }
        
        return {}
    
    def _extract_potential_weld_seams(self) -> List[Dict]:
        """
        提取潜在的焊缝边

        Returns:
            list: 潜在焊缝列表
        """
        potential_seams = []
        edge_face_map = self.topology.get('edge_face_map', {})
        
        # 遍历所有连接恰好两个面的边
        for edge_id, face_ids in edge_face_map.items():
            if len(face_ids) == 2:
                # 找到边数据
                edge_data = next((e for e in self.edges_data if e['id'] == edge_id), None)
                if not edge_data:
                    continue
                
                # 找到两个面的数据
                face1 = next((f for f in self.faces_data if f['id'] == face_ids[0]), None)
                face2 = next((f for f in self.faces_data if f['id'] == face_ids[1]), None)
                
                if not face1 or not face2:
                    continue
                
                # 计算两个面之间的角度（简化版）
                angle = self._calculate_face_angle(face1, face2)
                
                # 判断焊缝类型
                weld_type = self._classify_weld_type(angle)
                
                # 计算置信度（简化版）
                confidence = 0.8 if weld_type != "unknown" else 0.3
                
                seam_info = {
                    'edge_id': edge_id,
                    'edge_hash': edge_data['hash'],
                    'type': weld_type,
                    'confidence': confidence,
                    'properties': {
                        'gap': 0.0,  # 需要更精确的计算
                        'angle': angle,
                        'length': edge_data.get('length', 0.0),
                        'face1_id': face_ids[0],
                        'face2_id': face_ids[1],
                        'face1_type': face1['type'],
                        'face2_type': face2['type']
                    },
                    'adjacent_faces': face_ids
                }
                
                potential_seams.append(seam_info)
        
        return potential_seams
    
    def _calculate_face_angle(self, face1: Dict, face2: Dict) -> float:
        """
        计算两个面之间的角度（简化版）

        Args:
            face1: 面1数据
            face2: 面2数据

        Returns:
            float: 角度（度）
        """
        import math
        
        # 简化版：仅处理平面
        if face1['type'] == 'plane' and face2['type'] == 'plane':
            try:
                normal1 = face1['surface_data'].get('normal', [0, 0, 1])
                normal2 = face2['surface_data'].get('normal', [0, 0, 1])
                
                # 计算点积
                dot_product = sum(n1 * n2 for n1, n2 in zip(normal1, normal2))
                
                # 限制在 [-1, 1] 范围内
                dot_product = max(-1.0, min(1.0, dot_product))
                
                # 计算角度
                angle_rad = math.acos(dot_product)
                angle_deg = math.degrees(angle_rad)
                
                return angle_deg
            except:
                pass
        
        # 默认返回未知角度
        return 90.0
    
    def _classify_weld_type(self, angle: float) -> str:
        """
        根据角度分类焊缝类型

        Args:
            angle: 角度（度）

        Returns:
            str: 焊缝类型
        """
        if 160 <= angle <= 180:
            return "butt_joint"  # 对接焊缝
        elif 80 <= angle <= 100:
            return "corner_joint"  # 角接焊缝
        elif 85 <= angle <= 95:
            return "t_joint"  # T型接头
        elif angle < 30:
            return "lap_joint"  # 搭接焊缝
        else:
            return "unknown"
    
    def serialize_to_json_string(self, indent: int = None) -> str:
        """
        序列化为 JSON 字符串

        Args:
            indent: 缩进空格数，None 表示紧凑格式

        Returns:
            str: JSON 字符串
        """
        import json
        data = self.serialize()
        return json.dumps(data, indent=indent, ensure_ascii=False)


