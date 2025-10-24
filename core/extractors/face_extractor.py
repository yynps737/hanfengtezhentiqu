"""
面提取器
从 TopoDS_Shape 提取所有面信息，包括：
- 面的几何类型（平面、圆柱、圆锥、球面、B样条等）
- 面的曲面参数
- 面的边界边（外边界和内孔）
- 面的面积和方向
"""

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_WIRE
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Sphere, GeomAbs_Torus, GeomAbs_BezierSurface,
    GeomAbs_BSplineSurface, GeomAbs_SurfaceOfRevolution,
    GeomAbs_SurfaceOfExtrusion, GeomAbs_OffsetSurface,
    GeomAbs_OtherSurface
)
from OCC.Core.Geom import (
    Geom_Plane, Geom_CylindricalSurface, Geom_ConicalSurface,
    Geom_SphericalSurface, Geom_ToroidalSurface,
    Geom_BSplineSurface, Geom_BezierSurface,
    Geom_SurfaceOfRevolution, Geom_SurfaceOfLinearExtrusion
)
from OCC.Core.gp import gp_Pnt, gp_Dir
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from typing import List, Dict, Tuple, Optional


class FaceExtractor:
    """面提取器"""

    def __init__(self, shape, edge_extractor=None):
        """
        初始化面提取器

        Args:
            shape: TopoDS_Shape 对象
            edge_extractor: EdgeExtractor 实例（用于获取边ID）
        """
        if shape.IsNull():
            raise ValueError("输入形状为空")
        
        self.shape = shape
        self.edge_extractor = edge_extractor
        self.faces_data = []
        self.faces_map = {}  # {hash: TopoDS_Face}
        self.face_id_map = {}  # {hash: id}
        
    def extract(self) -> Tuple[List[Dict], Dict]:
        """
        提取所有面信息

        Returns:
            tuple: (faces_data, faces_map)
                faces_data: 面数据列表
                faces_map: 哈希到面对象的映射
        """
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        face_id = 0
        
        while explorer.More():
            face = topods.Face(explorer.Current())
            
            # 获取 OCC HashCode
            face_hash = hash(face.TShape())
            
            # 检查是否已经处理过这个面（去重）
            if face_hash not in self.face_id_map:
                # 提取面的几何信息
                face_data = self._extract_face_geometry(face, face_id, face_hash)
                
                if face_data:  # 只添加有效的面
                    self.faces_data.append(face_data)
                    self.faces_map[face_hash] = face
                    self.face_id_map[face_hash] = face_id
                    face_id += 1
            
            explorer.Next()
        
        print(f"✓ 提取面: {len(self.faces_data)} 个")
        return self.faces_data, self.faces_map
    
    def _extract_face_geometry(self, face, face_id: int, face_hash: int) -> Optional[Dict]:
        """
        提取单个面的几何信息

        Args:
            face: TopoDS_Face 对象
            face_id: 面ID
            face_hash: 面哈希值

        Returns:
            dict: 面数据，如果提取失败返回 None
        """
        try:
            # 获取面的曲面
            surface = BRep_Tool.Surface(face)
            
            if not surface:
                return None
            
            # 使用适配器获取曲面类型
            adaptor = BRepAdaptor_Surface(face)
            surface_type = self._get_surface_type(adaptor)
            
            # 提取曲面参数
            # 在新版 pythonocc-core 中，surface 本身就是 Geom_Surface 对象
            surface_data = self._extract_surface_parameters(
                adaptor,
                surface_type,
                surface
            )
            
            # 提取边界边（外边界）
            boundary_edges = self._extract_boundary_edges(face)
            
            # 提取内部边（孔）
            inner_edges = self._extract_inner_edges(face)
            
            # 计算面积
            area = self._calculate_face_area(face)
            
            # 获取面的方向
            orientation = self._get_face_orientation(face)
            
            face_data = {
                'id': face_id,
                'hash': face_hash,
                'type': surface_type,
                'boundary_edges': boundary_edges,
                'inner_edges': inner_edges,
                'surface_data': surface_data,
                'area': area,
                'orientation': orientation
            }
            
            return face_data
            
        except Exception as e:
            print(f"警告: 提取面 {face_id} 失败: {e}")
            return None
    
    def _get_surface_type(self, adaptor: BRepAdaptor_Surface) -> str:
        """
        获取曲面类型

        Args:
            adaptor: BRepAdaptor_Surface 对象

        Returns:
            str: 曲面类型字符串
        """
        surface_type = adaptor.GetType()
        
        type_map = {
            GeomAbs_Plane: "plane",
            GeomAbs_Cylinder: "cylinder",
            GeomAbs_Cone: "cone",
            GeomAbs_Sphere: "sphere",
            GeomAbs_Torus: "torus",
            GeomAbs_BezierSurface: "bezier",
            GeomAbs_BSplineSurface: "bspline",
            GeomAbs_SurfaceOfRevolution: "revolution",
            GeomAbs_SurfaceOfExtrusion: "extrusion",
            GeomAbs_OffsetSurface: "offset",
            GeomAbs_OtherSurface: "other"
        }
        
        return type_map.get(surface_type, "unknown")
    
    def _extract_boundary_edges(self, face) -> List[int]:
        """
        提取面的外边界边

        Args:
            face: TopoDS_Face 对象

        Returns:
            list: 外边界边ID列表
        """
        boundary_edges = []
        
        try:
            # 只获取外边界（第一个wire）
            from OCC.Core.BRepTools import breptools
            outer_wire = breptools.OuterWire(face)
            
            if not outer_wire.IsNull():
                edge_explorer = TopExp_Explorer(outer_wire, TopAbs_EDGE)
                
                while edge_explorer.More():
                    edge = topods.Edge(edge_explorer.Current())
                    edge_hash = hash(edge.TShape())
                    
                    if self.edge_extractor:
                        edge_id = self.edge_extractor.get_edge_id_by_hash(edge_hash)
                        if edge_id >= 0:
                            boundary_edges.append(edge_id)
                    
                    edge_explorer.Next()
        except Exception as e:
            print(f"警告: 提取边界边失败: {e}")
        
        return boundary_edges
    
    def _extract_inner_edges(self, face) -> List[List[int]]:
        """
        提取面的内部边（孔）

        Args:
            face: TopoDS_Face 对象

        Returns:
            list: 内部边ID列表的列表（每个孔一个列表）
        """
        inner_edges = []
        
        try:
            from OCC.Core.BRepTools import breptools
            outer_wire = breptools.OuterWire(face)
            
            # 遍历所有wire
            wire_explorer = TopExp_Explorer(face, TopAbs_WIRE)
            
            while wire_explorer.More():
                wire = topods.Wire(wire_explorer.Current())
                
                # 跳过外边界
                if wire.IsSame(outer_wire):
                    wire_explorer.Next()
                    continue
                
                # 提取内部孔的边
                hole_edges = []
                edge_explorer = TopExp_Explorer(wire, TopAbs_EDGE)
                
                while edge_explorer.More():
                    edge = topods.Edge(edge_explorer.Current())
                    edge_hash = hash(edge.TShape())
                    
                    if self.edge_extractor:
                        edge_id = self.edge_extractor.get_edge_id_by_hash(edge_hash)
                        if edge_id >= 0:
                            hole_edges.append(edge_id)
                    
                    edge_explorer.Next()
                
                if hole_edges:
                    inner_edges.append(hole_edges)
                
                wire_explorer.Next()
        except Exception as e:
            print(f"警告: 提取内部边失败: {e}")
        
        return inner_edges
    
    def _extract_surface_parameters(
        self,
        adaptor: BRepAdaptor_Surface,
        surface_type: str,
        surface
    ) -> Dict:
        """
        根据曲面类型提取参数

        Args:
            adaptor: BRepAdaptor_Surface 对象
            surface_type: 曲面类型
            surface: Geom_Surface 对象

        Returns:
            dict: 曲面参数
        """
        params = {}
        
        try:
            if surface_type == "plane":
                params = self._extract_plane_parameters(adaptor)
            elif surface_type == "cylinder":
                params = self._extract_cylinder_parameters(adaptor)
            elif surface_type == "cone":
                params = self._extract_cone_parameters(adaptor)
            elif surface_type == "sphere":
                params = self._extract_sphere_parameters(adaptor)
            elif surface_type == "torus":
                params = self._extract_torus_parameters(adaptor)
            elif surface_type == "bspline":
                params = self._extract_bspline_surface_parameters(surface)
            elif surface_type == "bezier":
                params = self._extract_bezier_surface_parameters(surface)
            elif surface_type == "revolution":
                params = self._extract_revolution_parameters(surface)
            elif surface_type == "extrusion":
                params = self._extract_extrusion_parameters(surface)
        except Exception as e:
            print(f"警告: 提取 {surface_type} 参数失败: {e}")
        
        return params
    
    def _extract_plane_parameters(self, adaptor: BRepAdaptor_Surface) -> Dict:
        """提取平面参数"""
        plane = adaptor.Plane()
        
        origin = plane.Location()
        normal = plane.Axis().Direction()
        x_axis = plane.XAxis().Direction()
        y_axis = plane.YAxis().Direction()
        
        return {
            'origin': [origin.X(), origin.Y(), origin.Z()],
            'normal': [normal.X(), normal.Y(), normal.Z()],
            'x_axis': [x_axis.X(), x_axis.Y(), x_axis.Z()],
            'y_axis': [y_axis.X(), y_axis.Y(), y_axis.Z()]
        }
    
    def _extract_cylinder_parameters(self, adaptor: BRepAdaptor_Surface) -> Dict:
        """提取圆柱面参数"""
        cylinder = adaptor.Cylinder()
        
        origin = cylinder.Location()
        axis = cylinder.Axis().Direction()
        radius = cylinder.Radius()
        
        return {
            'axis_origin': [origin.X(), origin.Y(), origin.Z()],
            'axis_direction': [axis.X(), axis.Y(), axis.Z()],
            'radius': radius
        }
    
    def _extract_cone_parameters(self, adaptor: BRepAdaptor_Surface) -> Dict:
        """提取圆锥面参数"""
        cone = adaptor.Cone()
        
        origin = cone.Location()
        axis = cone.Axis().Direction()
        radius = cone.RefRadius()
        semi_angle = cone.SemiAngle()
        
        return {
            'apex': [origin.X(), origin.Y(), origin.Z()],
            'axis_direction': [axis.X(), axis.Y(), axis.Z()],
            'ref_radius': radius,
            'semi_angle': semi_angle
        }
    
    def _extract_sphere_parameters(self, adaptor: BRepAdaptor_Surface) -> Dict:
        """提取球面参数"""
        sphere = adaptor.Sphere()
        
        center = sphere.Location()
        radius = sphere.Radius()
        
        return {
            'center': [center.X(), center.Y(), center.Z()],
            'radius': radius
        }
    
    def _extract_torus_parameters(self, adaptor: BRepAdaptor_Surface) -> Dict:
        """提取圆环面参数"""
        torus = adaptor.Torus()
        
        center = torus.Location()
        axis = torus.Axis().Direction()
        major_radius = torus.MajorRadius()
        minor_radius = torus.MinorRadius()
        
        return {
            'center': [center.X(), center.Y(), center.Z()],
            'axis': [axis.X(), axis.Y(), axis.Z()],
            'major_radius': major_radius,
            'minor_radius': minor_radius
        }
    
    def _extract_bspline_surface_parameters(self, surface) -> Dict:
        """提取B样条曲面参数"""
        bspline = Geom_BSplineSurface.DownCast(surface)
        if not bspline:
            return {}
        
        u_degree = bspline.UDegree()
        v_degree = bspline.VDegree()
        nb_u_poles = bspline.NbUPoles()
        nb_v_poles = bspline.NbVPoles()
        
        # 提取控制点网格
        control_points = []
        for i in range(1, nb_u_poles + 1):
            u_row = []
            for j in range(1, nb_v_poles + 1):
                pole = bspline.Pole(i, j)
                u_row.append([pole.X(), pole.Y(), pole.Z()])
            control_points.append(u_row)
        
        # 提取U方向节点
        nb_u_knots = bspline.NbUKnots()
        u_knots = []
        u_multiplicities = []
        for i in range(1, nb_u_knots + 1):
            u_knots.append(bspline.UKnot(i))
            u_multiplicities.append(bspline.UMultiplicity(i))
        
        # 提取V方向节点
        nb_v_knots = bspline.NbVKnots()
        v_knots = []
        v_multiplicities = []
        for i in range(1, nb_v_knots + 1):
            v_knots.append(bspline.VKnot(i))
            v_multiplicities.append(bspline.VMultiplicity(i))
        
        return {
            'u_degree': u_degree,
            'v_degree': v_degree,
            'control_points': control_points,
            'u_knots': u_knots,
            'u_multiplicities': u_multiplicities,
            'v_knots': v_knots,
            'v_multiplicities': v_multiplicities,
            'is_u_periodic': bspline.IsUPeriodic(),
            'is_v_periodic': bspline.IsVPeriodic(),
            'is_u_rational': bspline.IsURational(),
            'is_v_rational': bspline.IsVRational()
        }
    
    def _extract_bezier_surface_parameters(self, surface) -> Dict:
        """提取Bezier曲面参数"""
        bezier = Geom_BezierSurface.DownCast(surface)
        if not bezier:
            return {}
        
        u_degree = bezier.UDegree()
        v_degree = bezier.VDegree()
        nb_u_poles = bezier.NbUPoles()
        nb_v_poles = bezier.NbVPoles()
        
        # 提取控制点网格
        control_points = []
        for i in range(1, nb_u_poles + 1):
            u_row = []
            for j in range(1, nb_v_poles + 1):
                pole = bezier.Pole(i, j)
                u_row.append([pole.X(), pole.Y(), pole.Z()])
            control_points.append(u_row)
        
        return {
            'u_degree': u_degree,
            'v_degree': v_degree,
            'control_points': control_points,
            'is_u_rational': bezier.IsURational(),
            'is_v_rational': bezier.IsVRational()
        }
    
    def _extract_revolution_parameters(self, surface) -> Dict:
        """提取旋转曲面参数"""
        revolution = Geom_SurfaceOfRevolution.DownCast(surface)
        if not revolution:
            return {}
        
        axis_origin = revolution.Location()
        axis_direction = revolution.Direction()
        
        return {
            'axis_origin': [axis_origin.X(), axis_origin.Y(), axis_origin.Z()],
            'axis_direction': [axis_direction.X(), axis_direction.Y(), axis_direction.Z()]
        }
    
    def _extract_extrusion_parameters(self, surface) -> Dict:
        """提取拉伸曲面参数"""
        extrusion = Geom_SurfaceOfLinearExtrusion.DownCast(surface)
        if not extrusion:
            return {}
        
        direction = extrusion.Direction()
        
        return {
            'direction': [direction.X(), direction.Y(), direction.Z()]
        }
    
    def _calculate_face_area(self, face) -> float:
        """
        计算面的面积

        Args:
            face: TopoDS_Face 对象

        Returns:
            float: 面积
        """
        try:
            from OCC.Core.GProp import GProp_GProps
            from OCC.Core.BRepGProp import brepgprop
            
            props = GProp_GProps()
            brepgprop.SurfaceProperties(face, props)
            return props.Mass()  # 对于表面属性，Mass()返回面积
        except:
            return 0.0
    
    def _get_face_orientation(self, face) -> str:
        """
        获取面的方向

        Args:
            face: TopoDS_Face 对象

        Returns:
            str: "forward" 或 "reversed"
        """
        from OCC.Core.TopAbs import TopAbs_FORWARD, TopAbs_REVERSED
        
        orientation = face.Orientation()
        
        if orientation == TopAbs_FORWARD:
            return "forward"
        elif orientation == TopAbs_REVERSED:
            return "reversed"
        else:
            return "unknown"
    
    def get_faces_data(self) -> List[Dict]:
        """获取面数据列表"""
        return self.faces_data
    
    def get_faces_map(self) -> Dict:
        """获取面映射字典"""
        return self.faces_map
    
    def get_face_id_by_hash(self, face_hash: int) -> int:
        """
        根据哈希值获取面ID

        Args:
            face_hash: 面哈希值

        Returns:
            int: 面ID，如果不存在返回 -1
        """
        return self.face_id_map.get(face_hash, -1)

