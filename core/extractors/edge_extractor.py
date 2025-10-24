"""
边提取器
从 TopoDS_Shape 提取所有边信息，包括：
- 边的几何类型（直线、圆、B样条等）
- 边的起点和终点
- 边的曲线参数
- 边的相邻面（关键：用于焊缝识别）
"""

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GeomAbs import (
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse,
    GeomAbs_Hyperbola, GeomAbs_Parabola,
    GeomAbs_BezierCurve, GeomAbs_BSplineCurve,
    GeomAbs_OffsetCurve, GeomAbs_OtherCurve
)
from OCC.Core.Geom import (
    Geom_Line, Geom_Circle, Geom_Ellipse,
    Geom_BSplineCurve, Geom_BezierCurve
)
from OCC.Core.gp import gp_Pnt
from typing import List, Dict, Tuple, Optional
import math


class EdgeExtractor:
    """边提取器"""

    def __init__(self, shape, vertex_extractor=None):
        """
        初始化边提取器

        Args:
            shape: TopoDS_Shape 对象
            vertex_extractor: VertexExtractor 实例（用于获取顶点ID）
        """
        if shape.IsNull():
            raise ValueError("输入形状为空")
        
        self.shape = shape
        self.vertex_extractor = vertex_extractor
        self.edges_data = []
        self.edges_map = {}  # {hash: TopoDS_Edge}
        self.edge_id_map = {}  # {hash: id}
        
    def extract(self) -> Tuple[List[Dict], Dict]:
        """
        提取所有边信息

        Returns:
            tuple: (edges_data, edges_map)
                edges_data: 边数据列表
                edges_map: 哈希到边对象的映射
        """
        explorer = TopExp_Explorer(self.shape, TopAbs_EDGE)
        edge_id = 0
        
        while explorer.More():
            edge = topods.Edge(explorer.Current())
            
            # 获取 OCC HashCode
            edge_hash = hash(edge.TShape())
            
            # 检查是否已经处理过这个边（去重）
            if edge_hash not in self.edge_id_map:
                # 提取边的几何信息
                edge_data = self._extract_edge_geometry(edge, edge_id, edge_hash)
                
                if edge_data:  # 只添加有效的边
                    self.edges_data.append(edge_data)
                    self.edges_map[edge_hash] = edge
                    self.edge_id_map[edge_hash] = edge_id
                    edge_id += 1
            
            explorer.Next()
        
        print(f"✓ 提取边: {len(self.edges_data)} 条")
        return self.edges_data, self.edges_map
    
    def _extract_edge_geometry(self, edge, edge_id: int, edge_hash: int) -> Optional[Dict]:
        """
        提取单条边的几何信息

        Args:
            edge: TopoDS_Edge 对象
            edge_id: 边ID
            edge_hash: 边哈希值

        Returns:
            dict: 边数据，如果提取失败返回 None
        """
        try:
            # 获取边的曲线
            curve_handle, first_param, last_param = BRep_Tool.Curve(edge)
            
            if not curve_handle:
                return None
            
            # 获取起点和终点
            start_point = curve_handle.Value(first_param)
            end_point = curve_handle.Value(last_param)
            
            # 获取起点和终点的顶点ID
            vertices = self._get_edge_vertices(edge)
            
            # 获取曲线类型
            # 在新版 pythonocc-core 中，curve_handle 本身就是 Geom_Curve 对象
            curve_type = self._get_curve_type(curve_handle)
            
            # 提取曲线参数
            curve_data = self._extract_curve_parameters(
                curve_handle, 
                curve_type,
                start_point,
                end_point,
                first_param,
                last_param
            )
            
            # 计算边长度
            length = self._calculate_edge_length(edge)
            
            # 检查边的属性
            is_degenerated = BRep_Tool.Degenerated(edge)
            is_seam = BRep_Tool.IsClosed(edge)
            
            edge_data = {
                'id': edge_id,
                'hash': edge_hash,
                'type': curve_type,
                'vertices': vertices,
                'curve_data': curve_data,
                'length': length,
                'is_degenerated': is_degenerated,
                'is_seam': is_seam,
                'adjacent_faces': []  # 将在拓扑分析阶段填充
            }
            
            return edge_data
            
        except Exception as e:
            print(f"警告: 提取边 {edge_id} 失败: {e}")
            return None
    
    def _get_edge_vertices(self, edge) -> List[int]:
        """
        获取边的顶点ID列表

        Args:
            edge: TopoDS_Edge 对象

        Returns:
            list: 顶点ID列表 [start_vertex_id, end_vertex_id]
        """
        vertices = []
        
        try:
            # 获取边的顶点
            vertex_explorer = TopExp_Explorer(edge, TopAbs_VERTEX)
            
            while vertex_explorer.More():
                vertex = topods.Vertex(vertex_explorer.Current())
                vertex_hash = hash(vertex.TShape())
                
                if self.vertex_extractor:
                    vertex_id = self.vertex_extractor.get_vertex_id_by_hash(vertex_hash)
                    if vertex_id >= 0:
                        vertices.append(vertex_id)
                
                vertex_explorer.Next()
            
        except Exception as e:
            print(f"警告: 获取边顶点失败: {e}")
        
        return vertices
    
    def _get_curve_type(self, curve) -> str:
        """
        获取曲线类型

        Args:
            curve: Geom_Curve 对象

        Returns:
            str: 曲线类型字符串
        """
        try:
            # 尝试向下转型以确定具体类型
            if Geom_Line.DownCast(curve):
                return "line"
            elif Geom_Circle.DownCast(curve):
                return "circle"
            elif Geom_Ellipse.DownCast(curve):
                return "ellipse"
            elif Geom_BSplineCurve.DownCast(curve):
                return "bspline"
            elif Geom_BezierCurve.DownCast(curve):
                return "bezier"
            else:
                return "other"
        except:
            return "unknown"
    
    def _extract_curve_parameters(
        self,
        curve,
        curve_type: str,
        start_point: gp_Pnt,
        end_point: gp_Pnt,
        first_param: float,
        last_param: float
    ) -> Dict:
        """
        根据曲线类型提取参数

        Args:
            curve: Geom_Curve 对象
            curve_type: 曲线类型
            start_point: 起点
            end_point: 终点
            first_param: 起始参数
            last_param: 终止参数

        Returns:
            dict: 曲线参数
        """
        params = {
            'start': [start_point.X(), start_point.Y(), start_point.Z()],
            'end': [end_point.X(), end_point.Y(), end_point.Z()],
            'first_parameter': first_param,
            'last_parameter': last_param
        }
        
        try:
            if curve_type == "line":
                params.update(self._extract_line_parameters(curve))
            elif curve_type == "circle":
                params.update(self._extract_circle_parameters(curve, first_param, last_param))
            elif curve_type == "ellipse":
                params.update(self._extract_ellipse_parameters(curve))
            elif curve_type == "bspline":
                params.update(self._extract_bspline_parameters(curve))
            elif curve_type == "bezier":
                params.update(self._extract_bezier_parameters(curve))
        except Exception as e:
            print(f"警告: 提取 {curve_type} 参数失败: {e}")
        
        return params
    
    def _extract_line_parameters(self, curve) -> Dict:
        """提取直线参数"""
        line = Geom_Line.DownCast(curve)
        if not line:
            return {}
        
        # Geom_Line 的 Lin() 方法返回 gp_Lin 对象，它有 Direction() 方法
        gp_line = line.Lin()
        direction = gp_line.Direction()
        
        return {
            'direction': [direction.X(), direction.Y(), direction.Z()]
        }
    
    def _extract_circle_parameters(self, curve, first_param: float, last_param: float) -> Dict:
        """提取圆/圆弧参数"""
        circle = Geom_Circle.DownCast(curve)
        if not circle:
            return {}
        
        center = circle.Location()
        axis = circle.Axis().Direction()
        radius = circle.Radius()
        
        # 判断是否为完整圆
        param_range = abs(last_param - first_param)
        is_full_circle = abs(param_range - 2 * math.pi) < 1e-6
        
        return {
            'center': [center.X(), center.Y(), center.Z()],
            'axis': [axis.X(), axis.Y(), axis.Z()],
            'radius': radius,
            'start_angle': first_param,
            'end_angle': last_param,
            'is_full_circle': is_full_circle
        }
    
    def _extract_ellipse_parameters(self, curve) -> Dict:
        """提取椭圆参数"""
        ellipse = Geom_Ellipse.DownCast(curve)
        if not ellipse:
            return {}
        
        center = ellipse.Location()
        major_radius = ellipse.MajorRadius()
        minor_radius = ellipse.MinorRadius()
        
        return {
            'center': [center.X(), center.Y(), center.Z()],
            'major_radius': major_radius,
            'minor_radius': minor_radius
        }
    
    def _extract_bspline_parameters(self, curve) -> Dict:
        """提取B样条参数"""
        bspline = Geom_BSplineCurve.DownCast(curve)
        if not bspline:
            return {}
        
        degree = bspline.Degree()
        nb_poles = bspline.NbPoles()
        nb_knots = bspline.NbKnots()
        
        # 提取控制点
        control_points = []
        for i in range(1, nb_poles + 1):
            pole = bspline.Pole(i)
            control_points.append([pole.X(), pole.Y(), pole.Z()])
        
        # 提取节点向量
        knots = []
        multiplicities = []
        for i in range(1, nb_knots + 1):
            knots.append(bspline.Knot(i))
            multiplicities.append(bspline.Multiplicity(i))
        
        return {
            'degree': degree,
            'control_points': control_points,
            'knots': knots,
            'multiplicities': multiplicities,
            'is_rational': bspline.IsRational(),
            'is_periodic': bspline.IsPeriodic()
        }
    
    def _extract_bezier_parameters(self, curve) -> Dict:
        """提取Bezier曲线参数"""
        bezier = Geom_BezierCurve.DownCast(curve)
        if not bezier:
            return {}
        
        degree = bezier.Degree()
        nb_poles = bezier.NbPoles()
        
        # 提取控制点
        control_points = []
        for i in range(1, nb_poles + 1):
            pole = bezier.Pole(i)
            control_points.append([pole.X(), pole.Y(), pole.Z()])
        
        return {
            'degree': degree,
            'control_points': control_points,
            'is_rational': bezier.IsRational()
        }
    
    def _calculate_edge_length(self, edge) -> float:
        """
        计算边的长度

        Args:
            edge: TopoDS_Edge 对象

        Returns:
            float: 边长度
        """
        try:
            from OCC.Core.GProp import GProp_GProps
            from OCC.Core.BRepGProp import brepgprop
            
            props = GProp_GProps()
            brepgprop.LinearProperties(edge, props)
            return props.Mass()  # 对于线性属性，Mass()返回长度
        except:
            return 0.0
    
    def get_edges_data(self) -> List[Dict]:
        """获取边数据列表"""
        return self.edges_data
    
    def get_edges_map(self) -> Dict:
        """获取边映射字典"""
        return self.edges_map
    
    def get_edge_id_by_hash(self, edge_hash: int) -> int:
        """
        根据哈希值获取边ID

        Args:
            edge_hash: 边哈希值

        Returns:
            int: 边ID，如果不存在返回 -1
        """
        return self.edge_id_map.get(edge_hash, -1)

