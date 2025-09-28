"""
拓扑分析模块
负责构建和分析CAD模型的拓扑关系
"""

from OCC.Core.TopExp import topexp, TopExp_Explorer
from OCC.Core.TopTools import (
    TopTools_IndexedDataMapOfShapeListOfShape,
    TopTools_IndexedMapOfShape,
    TopTools_ListOfShape
)
from OCC.Core.TopAbs import (
    TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX,
    TopAbs_WIRE, TopAbs_SHELL, TopAbs_SOLID
)
from OCC.Core.TopoDS import topods


class TopologyAnalyzer:
    """拓扑分析器"""

    def __init__(self, shape):
        """
        初始化拓扑分析器

        Args:
            shape: TopoDS_Shape对象
        """
        self.shape = shape
        self.edge_face_map = None
        self.face_edge_map = None
        self.vertex_edge_map = None

    def build_edge_face_map(self):
        """构建边-面映射关系（核心功能）"""
        self.edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(
            self.shape,
            TopAbs_EDGE,
            TopAbs_FACE,
            self.edge_face_map
        )
        print(f"构建边-面映射完成: {self.edge_face_map.Size()} 条边")
        return self.edge_face_map

    def build_face_edge_map(self):
        """构建面-边映射关系"""
        self.face_edge_map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(
            self.shape,
            TopAbs_FACE,
            TopAbs_EDGE,
            self.face_edge_map
        )
        print(f"构建面-边映射完成: {self.face_edge_map.Size()} 个面")
        return self.face_edge_map

    def get_adjacent_faces(self, edge):
        """
        获取边的相邻面

        Args:
            edge: TopoDS_Edge对象

        Returns:
            faces: 相邻面列表
        """
        if self.edge_face_map is None:
            self.build_edge_face_map()

        faces = []
        index = self.edge_face_map.FindIndex(edge)
        if index > 0:
            face_list = self.edge_face_map.FindFromIndex(index)
            for i in range(face_list.Size()):
                faces.append(face_list.Value(i + 1))
        return faces

    def get_edges_with_two_faces(self):
        """
        获取所有恰好连接两个面的边（潜在焊缝位置）

        Returns:
            edges: [(edge, face1, face2), ...]
        """
        if self.edge_face_map is None:
            self.build_edge_face_map()

        result = []
        for i in range(1, self.edge_face_map.Size() + 1):
            edge = self.edge_face_map.FindKey(i)
            faces = self.edge_face_map.FindFromIndex(i)

            if faces.Size() == 2:
                face1 = faces.First()
                face2 = faces.Last()
                result.append((edge, face1, face2))

        print(f"找到 {len(result)} 条连接两个面的边")
        return result

    def count_topology_elements(self):
        """统计拓扑元素数量"""
        counts = {}

        # 统计各种拓扑元素
        for shape_type, name in [
            (TopAbs_VERTEX, "顶点"),
            (TopAbs_EDGE, "边"),
            (TopAbs_WIRE, "线框"),
            (TopAbs_FACE, "面"),
            (TopAbs_SHELL, "壳"),
            (TopAbs_SOLID, "实体")
        ]:
            explorer = TopExp_Explorer(self.shape, shape_type)
            count = 0
            while explorer.More():
                count += 1
                explorer.Next()
            counts[name] = count

        return counts

    def get_all_edges(self):
        """获取所有边"""
        edges = []
        explorer = TopExp_Explorer(self.shape, TopAbs_EDGE)
        while explorer.More():
            edge = topods.Edge(explorer.Current())
            edges.append(edge)
            explorer.Next()
        return edges

    def get_all_faces(self):
        """获取所有面"""
        faces = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        while explorer.More():
            face = topods.Face(explorer.Current())
            faces.append(face)
            explorer.Next()
        return faces