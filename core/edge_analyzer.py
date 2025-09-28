"""
边深度分析器
提取边及其相关的所有几何和拓扑信息
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.GCPnts import GCPnts_AbscissaPoint, GCPnts_UniformAbscissa
from OCC.Core.BRep import BRep_Tool
# from OCC.Core.BRepTools import breptools  # 注释掉可能有问题的导入
from OCC.Core.TopExp import topexp, TopExp_Explorer
from OCC.Core.TopAbs import (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE,
                             TopAbs_WIRE, TopAbs_SHELL, TopAbs_SOLID)
from OCC.Core.TopoDS import (topods, TopoDS_Edge, TopoDS_Face,
                             TopoDS_Vertex, TopoDS_Shape)
from OCC.Core.GeomAbs import (GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse,
                              GeomAbs_Hyperbola, GeomAbs_Parabola, GeomAbs_BezierCurve,
                              GeomAbs_BSplineCurve, GeomAbs_OtherCurve,
                              GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
                              GeomAbs_Sphere, GeomAbs_Torus, GeomAbs_BezierSurface,
                              GeomAbs_BSplineSurface)
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir
from OCC.Core.Precision import precision
from OCC.Core.GeomLProp import GeomLProp_CLProps, GeomLProp_SLProps
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Edge, ShapeAnalysis_Surface


class EdgeAnalyzer:
    """边深度分析器 - 提取所有可能的信息"""

    def __init__(self, shape: TopoDS_Shape, topology_analyzer=None):
        """
        初始化分析器

        Args:
            shape: 要分析的完整形状
            topology_analyzer: 可选的拓扑分析器实例（避免重复构建）
        """
        self.shape = shape
        self.edges_map = {}  # 边ID到边对象的映射

        # 如果没有提供拓扑分析器，创建一个
        if topology_analyzer is None:
            from .topology_analyzer import TopologyAnalyzer
            self.topology_analyzer = TopologyAnalyzer(shape)
        else:
            self.topology_analyzer = topology_analyzer

        self._build_edge_index()

    def _build_edge_index(self):
        """构建边的索引映射"""
        from OCC.Core.TopTools import TopTools_IndexedMapOfShape
        from OCC.Core.TopExp import topexp

        # 获取所有边
        edge_map = TopTools_IndexedMapOfShape()
        topexp.MapShapes(self.shape, TopAbs_EDGE, edge_map)

        # 建立边ID到边对象的映射
        for edge_idx in range(1, edge_map.Extent() + 1):
            edge = topods.Edge(edge_map.FindKey(edge_idx))
            edge_id = f"EDGE_{edge_idx - 1}"
            self.edges_map[edge_id] = edge

        print(f"边索引构建完成: {len(self.edges_map)} 条边")

    def get_edge_by_id(self, edge_id: str) -> Optional[TopoDS_Edge]:
        """根据ID获取边"""
        return self.edges_map.get(edge_id)

    def analyze_edge(self, edge_id: str) -> Dict[str, Any]:
        """
        深度分析指定边的所有信息

        Args:
            edge_id: 边的ID

        Returns:
            包含所有边信息的字典
        """
        edge = self.get_edge_by_id(edge_id)
        if not edge:
            return {"error": f"Edge {edge_id} not found"}

        analysis = {
            "edge_id": edge_id,
            "geometry": self._analyze_edge_geometry(edge),
            "topology": self._analyze_edge_topology(edge, edge_id),
            "vertices": self._analyze_edge_vertices(edge),
            "adjacent_faces": self._analyze_adjacent_faces(edge_id),
            "properties": self._analyze_edge_properties(edge),
            "parametric": self._analyze_parametric_info(edge),
            "quality": self._analyze_edge_quality(edge)
        }

        return analysis

    def _analyze_edge_geometry(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析边的几何信息"""
        curve = BRepAdaptor_Curve(edge)

        # 曲线类型
        curve_type = curve.GetType()
        type_names = {
            GeomAbs_Line: "直线",
            GeomAbs_Circle: "圆",
            GeomAbs_Ellipse: "椭圆",
            GeomAbs_Hyperbola: "双曲线",
            GeomAbs_Parabola: "抛物线",
            GeomAbs_BezierCurve: "贝塞尔曲线",
            GeomAbs_BSplineCurve: "B样条曲线",
            GeomAbs_OtherCurve: "其他曲线"
        }

        geometry = {
            "type": type_names.get(curve_type, "未知"),
            "type_code": int(curve_type),
            "is_closed": BRep_Tool.IsClosed(edge),
            "is_degenerated": BRep_Tool.Degenerated(edge),
        }

        # 长度
        length = GCPnts_AbscissaPoint.Length(
            curve,
            curve.FirstParameter(),
            curve.LastParameter()
        )
        geometry["length"] = float(length)

        # 参数范围
        geometry["parameter_range"] = {
            "first": float(curve.FirstParameter()),
            "last": float(curve.LastParameter())
        }

        # 起点、中点、终点
        first_pnt = curve.Value(curve.FirstParameter())
        last_pnt = curve.Value(curve.LastParameter())
        mid_param = (curve.FirstParameter() + curve.LastParameter()) / 2
        mid_pnt = curve.Value(mid_param)

        geometry["points"] = {
            "start": [float(first_pnt.X()), float(first_pnt.Y()), float(first_pnt.Z())],
            "middle": [float(mid_pnt.X()), float(mid_pnt.Y()), float(mid_pnt.Z())],
            "end": [float(last_pnt.X()), float(last_pnt.Y()), float(last_pnt.Z())]
        }

        # 如果是特定类型，获取额外信息
        if curve_type == GeomAbs_Circle:
            circle = curve.Circle()
            geometry["circle_info"] = {
                "center": [float(circle.Location().X()),
                          float(circle.Location().Y()),
                          float(circle.Location().Z())],
                "radius": float(circle.Radius()),
                "axis": [float(circle.Axis().Direction().X()),
                        float(circle.Axis().Direction().Y()),
                        float(circle.Axis().Direction().Z())]
            }
        elif curve_type == GeomAbs_Line:
            line = curve.Line()
            geometry["line_info"] = {
                "origin": [float(line.Location().X()),
                          float(line.Location().Y()),
                          float(line.Location().Z())],
                "direction": [float(line.Direction().X()),
                             float(line.Direction().Y()),
                             float(line.Direction().Z())]
            }

        # 曲率信息
        geometry["curvature"] = self._calculate_curvature(curve, mid_param)

        return geometry

    def _analyze_edge_topology(self, edge: TopoDS_Edge, edge_id: str) -> Dict[str, Any]:
        """分析边的拓扑信息"""
        # 使用TopologyAnalyzer获取邻接面
        faces = self.topology_analyzer.get_adjacent_faces(edge)

        topology = {
            "adjacent_face_count": len(faces),
            "orientation": str(edge.Orientation()),
            "is_seam": False,  # 需要根据面判断
            "is_manifold": True  # 默认为流形
        }

        # 检查是否为缝合边
        if len(faces) == 1:
            face = topods.Face(faces[0])
            if BRep_Tool.IsClosed(edge, face):
                topology["is_seam"] = True

        # 判断流形性
        if len(faces) > 2:
            topology["is_manifold"] = False

        return topology

    def _analyze_edge_vertices(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析边的顶点信息"""
        vertices = {"start": None, "end": None}

        # 获取顶点
        explorer = TopExp_Explorer(edge, TopAbs_VERTEX)
        vertex_list = []
        while explorer.More():
            vertex = topods.Vertex(explorer.Current())
            pnt = BRep_Tool.Pnt(vertex)
            tolerance = BRep_Tool.Tolerance(vertex)

            vertex_info = {
                "coordinates": [float(pnt.X()), float(pnt.Y()), float(pnt.Z())],
                "tolerance": float(tolerance)
            }
            vertex_list.append(vertex_info)
            explorer.Next()

        if len(vertex_list) >= 1:
            vertices["start"] = vertex_list[0]
        if len(vertex_list) >= 2:
            vertices["end"] = vertex_list[1]
        elif len(vertex_list) == 1:
            vertices["end"] = vertex_list[0]  # 闭合边

        vertices["count"] = len(vertex_list)
        vertices["is_closed"] = (len(vertex_list) == 1)

        return vertices

    def _analyze_adjacent_faces(self, edge_id: str) -> List[Dict[str, Any]]:
        """深度分析邻接面信息"""
        # 获取边对象
        edge = self.edges_map.get(edge_id)
        if not edge:
            return []

        # 使用TopologyAnalyzer获取邻接面
        faces = self.topology_analyzer.get_adjacent_faces(edge)
        faces_info = []

        for i, face_shape in enumerate(faces):
            face = topods.Face(face_shape)
            face_info = {
                "face_index": i,
                "geometry": self._analyze_face_geometry(face),
                "properties": self._analyze_face_properties(face)
            }
            faces_info.append(face_info)

        return faces_info

    def _analyze_face_geometry(self, face: TopoDS_Face) -> Dict[str, Any]:
        """分析面的几何信息"""
        surface = BRepAdaptor_Surface(face)

        # 表面类型
        surface_type = surface.GetType()
        type_names = {
            GeomAbs_Plane: "平面",
            GeomAbs_Cylinder: "圆柱面",
            GeomAbs_Cone: "圆锥面",
            GeomAbs_Sphere: "球面",
            GeomAbs_Torus: "环面",
            GeomAbs_BezierSurface: "贝塞尔曲面",
            GeomAbs_BSplineSurface: "B样条曲面"
        }

        geometry = {
            "type": type_names.get(surface_type, "其他曲面"),
            "type_code": int(surface_type),
            "is_closed_u": surface.IsUClosed(),
            "is_closed_v": surface.IsVClosed()
        }

        # UV参数范围
        geometry["uv_range"] = {
            "u_min": float(surface.FirstUParameter()),
            "u_max": float(surface.LastUParameter()),
            "v_min": float(surface.FirstVParameter()),
            "v_max": float(surface.LastVParameter())
        }

        # 面积
        props = GProp_GProps()
        brepgprop.SurfaceProperties(face, props)
        geometry["area"] = float(props.Mass())

        # 质心
        centroid = props.CentreOfMass()
        geometry["centroid"] = [float(centroid.X()),
                               float(centroid.Y()),
                               float(centroid.Z())]

        # 法向量（在中心点）
        u_mid = (surface.FirstUParameter() + surface.LastUParameter()) / 2
        v_mid = (surface.FirstVParameter() + surface.LastVParameter()) / 2

        try:
            props_srf = GeomLProp_SLProps(
                surface.Surface().Surface(),
                u_mid, v_mid,
                1,
                precision.Confusion()
            )

            if props_srf.IsNormalDefined():
                normal = props_srf.Normal()
                geometry["normal_at_center"] = [
                    float(normal.X()),
                    float(normal.Y()),
                    float(normal.Z())
                ]
        except:
            geometry["normal_at_center"] = None

        # 特定表面类型的额外信息
        if surface_type == GeomAbs_Plane:
            plane = surface.Plane()
            geometry["plane_info"] = {
                "origin": [float(plane.Location().X()),
                          float(plane.Location().Y()),
                          float(plane.Location().Z())],
                "normal": [float(plane.Axis().Direction().X()),
                          float(plane.Axis().Direction().Y()),
                          float(plane.Axis().Direction().Z())]
            }
        elif surface_type == GeomAbs_Cylinder:
            cylinder = surface.Cylinder()
            geometry["cylinder_info"] = {
                "center": [float(cylinder.Location().X()),
                          float(cylinder.Location().Y()),
                          float(cylinder.Location().Z())],
                "radius": float(cylinder.Radius()),
                "axis": [float(cylinder.Axis().Direction().X()),
                        float(cylinder.Axis().Direction().Y()),
                        float(cylinder.Axis().Direction().Z())]
            }

        return geometry

    def _analyze_face_properties(self, face: TopoDS_Face) -> Dict[str, Any]:
        """分析面的属性"""
        properties = {}

        # 边界框
        box = Bnd_Box()
        brepbndlib.Add(face, box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()

        properties["bounding_box"] = {
            "min": [float(xmin), float(ymin), float(zmin)],
            "max": [float(xmax), float(ymax), float(zmax)],
            "diagonal": float(np.sqrt((xmax-xmin)**2 + (ymax-ymin)**2 + (zmax-zmin)**2))
        }

        # 边数
        edge_count = 0
        explorer = TopExp_Explorer(face, TopAbs_EDGE)
        while explorer.More():
            edge_count += 1
            explorer.Next()
        properties["edge_count"] = edge_count

        # 顶点数
        vertex_count = 0
        explorer = TopExp_Explorer(face, TopAbs_VERTEX)
        while explorer.More():
            vertex_count += 1
            explorer.Next()
        properties["vertex_count"] = vertex_count

        # 方向
        properties["orientation"] = str(face.Orientation())

        return properties

    def _analyze_edge_properties(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析边的物理属性"""
        properties = {}

        # 边界框
        box = Bnd_Box()
        brepbndlib.Add(edge, box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()

        properties["bounding_box"] = {
            "min": [float(xmin), float(ymin), float(zmin)],
            "max": [float(xmax), float(ymax), float(zmax)],
            "diagonal": float(np.sqrt((xmax-xmin)**2 + (ymax-ymin)**2 + (zmax-zmin)**2))
        }

        # 容差
        properties["tolerance"] = float(BRep_Tool.Tolerance(edge))

        # 质量属性
        props = GProp_GProps()
        brepgprop.LinearProperties(edge, props)
        properties["linear_mass"] = float(props.Mass())

        # 质心
        if props.Mass() > 0:
            centroid = props.CentreOfMass()
            properties["centroid"] = [float(centroid.X()),
                                     float(centroid.Y()),
                                     float(centroid.Z())]

        return properties

    def _analyze_parametric_info(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析参数信息"""
        curve = BRepAdaptor_Curve(edge)

        parametric = {}

        # 采样点（均匀分布10个点）
        num_samples = 10
        samples = []
        for i in range(num_samples):
            t = curve.FirstParameter() + \
                (curve.LastParameter() - curve.FirstParameter()) * i / (num_samples - 1)
            pnt = curve.Value(t)
            samples.append({
                "parameter": float(t),
                "point": [float(pnt.X()), float(pnt.Y()), float(pnt.Z())]
            })

        parametric["sample_points"] = samples

        # 导数信息（在中点）
        mid_param = (curve.FirstParameter() + curve.LastParameter()) / 2
        try:
            pnt = gp_Pnt()
            vec1 = gp_Vec()
            vec2 = gp_Vec()
            curve.D2(mid_param, pnt, vec1, vec2)

            parametric["derivatives_at_midpoint"] = {
                "first_derivative": [float(vec1.X()), float(vec1.Y()), float(vec1.Z())],
                "second_derivative": [float(vec2.X()), float(vec2.Y()), float(vec2.Z())],
                "tangent_magnitude": float(vec1.Magnitude())
            }
        except:
            parametric["derivatives_at_midpoint"] = None

        return parametric

    def _analyze_edge_quality(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析边的质量"""
        quality = {}

        # 使用ShapeAnalysis检查
        sa_edge = ShapeAnalysis_Edge()

        # 检查是否有小边
        curve = BRepAdaptor_Curve(edge)
        length = GCPnts_AbscissaPoint.Length(
            curve,
            curve.FirstParameter(),
            curve.LastParameter()
        )

        quality["is_small_edge"] = length < 1e-6
        quality["length_quality"] = "极小" if length < 0.001 else \
                                   "小" if length < 0.1 else \
                                   "中等" if length < 10 else "大"

        # 曲率变化
        quality["curvature_variation"] = self._analyze_curvature_variation(edge)

        return quality

    def _calculate_curvature(self, curve: BRepAdaptor_Curve, param: float) -> Optional[float]:
        """计算指定参数处的曲率"""
        try:
            pnt = gp_Pnt()
            vec1 = gp_Vec()
            vec2 = gp_Vec()
            curve.D2(param, pnt, vec1, vec2)

            # 曲率 = |v1 × v2| / |v1|^3
            cross_prod = vec1.Crossed(vec2)
            v1_mag = vec1.Magnitude()

            if v1_mag > 1e-10:
                curvature = cross_prod.Magnitude() / (v1_mag ** 3)
                return float(curvature)
        except:
            pass

        return None

    def _analyze_curvature_variation(self, edge: TopoDS_Edge) -> Dict[str, Any]:
        """分析曲率变化"""
        curve = BRepAdaptor_Curve(edge)

        # 在边上采样计算曲率
        num_samples = 20
        curvatures = []

        for i in range(num_samples):
            t = curve.FirstParameter() + \
                (curve.LastParameter() - curve.FirstParameter()) * i / (num_samples - 1)
            curv = self._calculate_curvature(curve, t)
            if curv is not None:
                curvatures.append(curv)

        if curvatures:
            return {
                "min": float(min(curvatures)),
                "max": float(max(curvatures)),
                "mean": float(np.mean(curvatures)),
                "std": float(np.std(curvatures))
            }

        return {"min": 0, "max": 0, "mean": 0, "std": 0}

    def analyze_multiple_edges(self, edge_ids: List[str]) -> List[Dict[str, Any]]:
        """批量分析多条边"""
        results = []
        for edge_id in edge_ids:
            results.append(self.analyze_edge(edge_id))
        return results

    def get_all_edges_list(self) -> List[Dict[str, str]]:
        """获取所有边的简要列表"""
        edges_list = []
        for edge_id, edge in self.edges_map.items():
            curve = BRepAdaptor_Curve(edge)
            length = GCPnts_AbscissaPoint.Length(
                curve,
                curve.FirstParameter(),
                curve.LastParameter()
            )

            curve_type = curve.GetType()
            type_names = {
                GeomAbs_Line: "直线",
                GeomAbs_Circle: "圆",
                GeomAbs_Ellipse: "椭圆",
                GeomAbs_BSplineCurve: "B样条",
            }

            # 使用TopologyAnalyzer获取邻接面数量
            faces = self.topology_analyzer.get_adjacent_faces(edge)

            edges_list.append({
                "id": edge_id,
                "type": type_names.get(curve_type, "其他"),
                "length": round(length, 3),
                "faces": len(faces)
            })

        return edges_list