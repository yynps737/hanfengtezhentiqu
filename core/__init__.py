"""
核心模块 - 几何提取和拓扑分析

主要功能：
1. STEP 文件加载
2. 几何提取（顶点、边、面）
3. 拓扑分析（邻接关系）
4. 数据序列化

架构说明：
- GeometryExtractor: 提取完整几何和拓扑信息
- 保持 OCC 的精确几何类型和参数
- 支持焊缝识别所需的拓扑关系
- 前端自行决定如何渲染（网格/精确几何）
"""

from .step_loader import StepLoader
from .geometry_extractor import GeometryExtractor

# 导出子模块
from . import extractors
from . import topology
from . import serializers

__all__ = [
    'StepLoader',
    'GeometryExtractor',
    'extractors',
    'topology',
    'serializers',
]