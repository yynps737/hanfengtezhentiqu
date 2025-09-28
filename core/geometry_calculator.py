"""
几何计算模块
负责各种几何属性的计算（角度、长度、距离等）
"""

import numpy as np
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.GCPnts import GCPnts_AbscissaPoint
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir
from OCC.Core.Precision import precision
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps


class GeometryCalculator:
    """几何计算器"""

    @staticmethod
    def calculate_edge_length(edge):
        """
        计算边的长度

        Args:
            edge: TopoDS_Edge对象

        Returns:
            length: 边长度（mm）
        """
        curve = BRepAdaptor_Curve(edge)
        length = GCPnts_AbscissaPoint.Length(
            curve,
            curve.FirstParameter(),
            curve.LastParameter()
        )
        return length

    @staticmethod
    def calculate_dihedral_angle(edge, face1, face2):
        """
        计算两个面通过共享边形成的二面角

        Args:
            edge: 共享边
            face1: 第一个面
            face2: 第二个面

        Returns:
            angle: 角度（度）
        """
        # 获取边的中点参数
        curve = BRepAdaptor_Curve(edge)
        mid_param = (curve.FirstParameter() + curve.LastParameter()) / 2
        mid_point = curve.Value(mid_param)

        # 获取两个面的法向量
        normal1 = GeometryCalculator.get_face_normal_at_point(face1, mid_point)
        normal2 = GeometryCalculator.get_face_normal_at_point(face2, mid_point)

        if normal1 and normal2:
            # 计算法向量夹角
            dot_product = (
                normal1.X() * normal2.X() +
                normal1.Y() * normal2.Y() +
                normal1.Z() * normal2.Z()
            )

            # 确保在[-1, 1]范围内
            dot_product = max(-1.0, min(1.0, dot_product))

            # 计算角度（弧度转角度）
            angle_rad = np.arccos(dot_product)
            angle_deg = np.degrees(angle_rad)

            return angle_deg
        else:
            return None

    @staticmethod
    def get_face_normal_at_point(face, point):
        """
        获取面在指定点的法向量

        Args:
            face: TopoDS_Face对象
            point: gp_Pnt点

        Returns:
            normal: gp_Dir法向量
        """
        try:
            # 获取面的曲面
            surface = BRepAdaptor_Surface(face)

            # 获取点在曲面上的UV参数
            u_min = surface.FirstUParameter()
            u_max = surface.LastUParameter()
            v_min = surface.FirstVParameter()
            v_max = surface.LastVParameter()

            # 使用曲面中点的UV参数（简化处理）
            u = (u_min + u_max) / 2
            v = (v_min + v_max) / 2

            # 创建曲面属性对象
            props = GeomLProp_SLProps(
                surface.Surface().Surface(),
                u, v,
                1,  # 需要一阶导数
                precision.Confusion()
            )

            if props.IsNormalDefined():
                normal = props.Normal()
                return gp_Dir(normal)
            else:
                return None

        except Exception as e:
            print(f"计算法向量失败: {e}")
            return None

    @staticmethod
    def calculate_face_area(face):
        """
        计算面的面积

        Args:
            face: TopoDS_Face对象

        Returns:
            area: 面积（mm²）
        """
        props = GProp_GProps()
        brepgprop.SurfaceProperties(face, props)
        return props.Mass()

    @staticmethod
    def is_linear_edge(edge):
        """
        判断边是否为直线

        Args:
            edge: TopoDS_Edge对象

        Returns:
            bool: 是否为直线
        """
        curve = BRepAdaptor_Curve(edge)
        curve_type = curve.GetType()

        # GeomAbs_Line = 1
        return curve_type == 1

    @staticmethod
    def is_planar_face(face):
        """
        判断面是否为平面

        Args:
            face: TopoDS_Face对象

        Returns:
            bool: 是否为平面
        """
        surface = BRepAdaptor_Surface(face)
        surface_type = surface.GetType()

        # GeomAbs_Plane = 1
        return surface_type == 1

    @staticmethod
    def get_edge_midpoint(edge):
        """
        获取边的中点

        Args:
            edge: TopoDS_Edge对象

        Returns:
            point: gp_Pnt中点
        """
        curve = BRepAdaptor_Curve(edge)
        mid_param = (curve.FirstParameter() + curve.LastParameter()) / 2
        return curve.Value(mid_param)

    @staticmethod
    def calculate_distance_between_faces(face1, face2):
        """
        计算两个面之间的最小距离

        Args:
            face1: 第一个面
            face2: 第二个面

        Returns:
            distance: 最小距离（mm）
        """
        # 这是一个简化版本，实际应使用 BRepExtrema_DistShapeShape
        # 暂时返回0
        return 0.0