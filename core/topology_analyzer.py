"""
拓扑分析模块 - 极简版
负责构建和分析CAD模型的拓扑关系
"""

from OCC.Core.TopExp import topexp
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE


class TopologyAnalyzer:
    """拓扑分析器 - 仅保留边-面映射核心功能"""

    def __init__(self, shape):
        """
        初始化拓扑分析器

        参数:
            shape: TopoDS_Shape对象
        """
        self.shape = shape
        self.edge_face_map = None

    def build_edge_face_map(self):
        """构建边-面映射关系（核心功能）"""
        self.edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(
            self.shape,
            TopAbs_EDGE,
            TopAbs_FACE,
            self.edge_face_map
        )
        print(f"构建边-面映射: {self.edge_face_map.Size()} 条边")
        return self.edge_face_map

    def get_adjacent_faces(self, edge):
        """
        获取边的相邻面

        参数:
            edge: TopoDS_Edge对象

        返回:
            list: 相邻面列表
        """
        if self.edge_face_map is None:
            self.build_edge_face_map()

        faces = []
        index = self.edge_face_map.FindIndex(edge)
        if index > 0:
            face_list = self.edge_face_map.FindFromIndex(index)
            # 遍历面列表
            from OCC.Core.TopTools import TopTools_ListIteratorOfListOfShape
            iterator = TopTools_ListIteratorOfListOfShape(face_list)
            while iterator.More():
                faces.append(iterator.Value())
                iterator.Next()
        return faces