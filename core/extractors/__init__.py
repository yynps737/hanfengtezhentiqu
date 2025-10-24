"""
几何提取器模块
从 TopoDS_Shape 提取精确的几何和拓扑信息
"""

from .vertex_extractor import VertexExtractor
from .edge_extractor import EdgeExtractor
from .face_extractor import FaceExtractor

__all__ = [
    'VertexExtractor',
    'EdgeExtractor',
    'FaceExtractor',
]


