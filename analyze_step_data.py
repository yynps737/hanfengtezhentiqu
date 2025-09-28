#!/usr/bin/env python3
"""
分析STEP文件导入后PythonOCC能够访问的所有拓扑和几何数据
"""

from OCC.Core.TopExp import TopExp_Explorer, topexp
from OCC.Core.TopAbs import (
    TopAbs_COMPOUND, TopAbs_COMPSOLID, TopAbs_SOLID,
    TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE,
    TopAbs_EDGE, TopAbs_VERTEX
)
from OCC.Core.TopoDS import topods
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.GeomAbs import (
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse, GeomAbs_Hyperbola,
    GeomAbs_Parabola, GeomAbs_BezierCurve, GeomAbs_BSplineCurve,
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere,
    GeomAbs_Torus, GeomAbs_BezierSurface, GeomAbs_BSplineSurface
)
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt
from OCC.Core.TopTools import TopTools_IndexedMapOfShape, TopTools_IndexedDataMapOfShapeListOfShape

def analyze_topology_hierarchy():
    """分析STEP导入后的拓扑层次结构"""

    print("\n" + "="*70)
    print("STEP文件导入后的拓扑层次结构")
    print("="*70)

    print("\nOCCT的拓扑层次（从高到低）：")
    print("""
    COMPOUND (复合体)
        ↓
    COMPSOLID (复合实体)
        ↓
    SOLID (实体) - 封闭的体积
        ↓
    SHELL (壳) - 连接的面集合
        ↓
    FACE (面) - 带边界的曲面
        ↓
    WIRE (线框) - 连接的边集合
        ↓
    EDGE (边) - 参数化曲线
        ↓
    VERTEX (顶点) - 3D空间中的点
    """)

    print("\n通过TopExp_Explorer可以遍历获取每一层的所有元素")

def analyze_available_topology_data():
    """分析可获取的拓扑数据"""

    print("\n" + "="*70)
    print("从TopoDS_Shape可以获取的拓扑数据")
    print("="*70)

    print("\n1. 基本拓扑元素获取：")
    print("""
    # 获取所有顶点
    explorer = TopExp_Explorer(shape, TopAbs_VERTEX)
    while explorer.More():
        vertex = topods.Vertex(explorer.Current())
        # 获取顶点坐标
        pnt = BRep_Tool.Pnt(vertex)
        x, y, z = pnt.X(), pnt.Y(), pnt.Z()
        explorer.Next()

    # 获取所有边
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        edge = topods.Edge(explorer.Current())
        explorer.Next()

    # 获取所有面
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = topods.Face(explorer.Current())
        explorer.Next()
    """)

    print("\n2. 拓扑关系映射：")
    print("""
    # 构建边-面映射（哪些边属于哪些面）
    edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp.MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)

    # 构建顶点-边映射（哪些顶点连接哪些边）
    vertex_edge_map = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp.MapShapesAndAncestors(shape, TopAbs_VERTEX, TopAbs_EDGE, vertex_edge_map)

    # 构建边-实体映射
    edge_solid_map = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp.MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_SOLID, edge_solid_map)
    """)

    print("\n3. 拓扑查询功能：")
    print("""
    # 获取面的所有边界边
    wire = BRepTools.OuterWire(face)
    edge_explorer = TopExp_Explorer(wire, TopAbs_EDGE)

    # 获取边的起止顶点
    v1 = topexp.FirstVertex(edge)
    v2 = topexp.LastVertex(edge)

    # 判断边是否封闭
    is_closed = BRep_Tool.IsClosed(edge)

    # 判断面的朝向
    orientation = face.Orientation()  # FORWARD, REVERSED, INTERNAL, EXTERNAL
    """)

def analyze_geometric_data():
    """分析可获取的几何数据"""

    print("\n" + "="*70)
    print("从拓扑元素可以获取的几何数据")
    print("="*70)

    print("\n1. 顶点(VERTEX)的几何数据：")
    print("""
    vertex = topods.Vertex(...)
    # 获取3D坐标
    point = BRep_Tool.Pnt(vertex)
    x, y, z = point.X(), point.Y(), point.Z()

    # 获取公差
    tolerance = BRep_Tool.Tolerance(vertex)
    """)

    print("\n2. 边(EDGE)的几何数据：")
    print("""
    edge = topods.Edge(...)

    # 创建曲线适配器
    curve = BRepAdaptor_Curve(edge)

    # 获取曲线类型
    curve_type = curve.GetType()
    # GeomAbs_Line (直线)
    # GeomAbs_Circle (圆)
    # GeomAbs_Ellipse (椭圆)
    # GeomAbs_Hyperbola (双曲线)
    # GeomAbs_Parabola (抛物线)
    # GeomAbs_BezierCurve (贝塞尔曲线)
    # GeomAbs_BSplineCurve (B样条曲线)
    # GeomAbs_OtherCurve (其他)

    # 获取参数范围
    first_param = curve.FirstParameter()
    last_param = curve.LastParameter()

    # 获取曲线长度
    from OCC.Core.GCPnts import GCPnts_AbscissaPoint
    length = GCPnts_AbscissaPoint.Length(curve, first_param, last_param)

    # 获取曲线上任意点
    param = (first_param + last_param) / 2  # 中点参数
    point = curve.Value(param)  # gp_Pnt

    # 获取切向量
    from OCC.Core.BRepLProp import BRepLProp_CLProps
    props = BRepLProp_CLProps(curve, param, 1, 1e-6)
    tangent = props.D1()  # 一阶导数（切向量）

    # 如果是直线，获取方向
    if curve_type == GeomAbs_Line:
        line = curve.Line()
        direction = line.Direction()

    # 如果是圆，获取圆心和半径
    if curve_type == GeomAbs_Circle:
        circle = curve.Circle()
        center = circle.Location()
        radius = circle.Radius()
    """)

    print("\n3. 面(FACE)的几何数据：")
    print("""
    face = topods.Face(...)

    # 创建曲面适配器
    surface = BRepAdaptor_Surface(face)

    # 获取曲面类型
    surface_type = surface.GetType()
    # GeomAbs_Plane (平面)
    # GeomAbs_Cylinder (圆柱面)
    # GeomAbs_Cone (圆锥面)
    # GeomAbs_Sphere (球面)
    # GeomAbs_Torus (环面)
    # GeomAbs_BezierSurface (贝塞尔曲面)
    # GeomAbs_BSplineSurface (B样条曲面)
    # GeomAbs_SurfaceOfRevolution (旋转曲面)
    # GeomAbs_SurfaceOfExtrusion (拉伸曲面)
    # GeomAbs_OtherSurface (其他)

    # 获取UV参数范围
    u_min = surface.FirstUParameter()
    u_max = surface.LastUParameter()
    v_min = surface.FirstVParameter()
    v_max = surface.LastVParameter()

    # 获取面上任意点
    u = (u_min + u_max) / 2
    v = (v_min + v_max) / 2
    point = surface.Value(u, v)  # gp_Pnt

    # 获取法向量
    from OCC.Core.GeomLProp import GeomLProp_SLProps
    props = GeomLProp_SLProps(surface.Surface().Surface(), u, v, 1, 1e-6)
    if props.IsNormalDefined():
        normal = props.Normal()  # gp_Dir

    # 获取面积
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop
    props = GProp_GProps()
    brepgprop.SurfaceProperties(face, props)
    area = props.Mass()

    # 如果是平面，获取平面参数
    if surface_type == GeomAbs_Plane:
        plane = surface.Plane()
        location = plane.Location()  # 平面上一点
        normal = plane.Axis().Direction()  # 法向量

    # 如果是圆柱面，获取轴线和半径
    if surface_type == GeomAbs_Cylinder:
        cylinder = surface.Cylinder()
        axis = cylinder.Axis()
        radius = cylinder.Radius()
    """)

def analyze_advanced_topology():
    """分析高级拓扑查询"""

    print("\n" + "="*70)
    print("高级拓扑查询功能")
    print("="*70)

    print("\n1. 拓扑连通性分析：")
    print("""
    # 检查两个面是否共享边
    from OCC.Core.TopExp import topexp
    edge = topexp.CommonEdge(face1, face2)

    # 获取实体的所有外表面
    shell = BRepTools.OuterShell(solid)

    # 检查形状是否有效
    from OCC.Core.BRepCheck import BRepCheck_Analyzer
    analyzer = BRepCheck_Analyzer(shape)
    is_valid = analyzer.IsValid()
    """)

    print("\n2. 拓扑遍历和过滤：")
    print("""
    # 获取特定类型的所有子形状
    from OCC.Core.TopTools import TopTools_ListOfShape
    faces = TopTools_ListOfShape()
    topexp.MapShapes(shape, TopAbs_FACE, faces)

    # 获取形状的包围盒
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    """)

def main():
    """主函数"""
    print("\n" + "="*70)
    print("STEP文件导入后PythonOCC可访问的完整数据")
    print("="*70)

    # 分析拓扑层次
    analyze_topology_hierarchy()

    # 分析拓扑数据
    analyze_available_topology_data()

    # 分析几何数据
    analyze_geometric_data()

    # 分析高级功能
    analyze_advanced_topology()

    print("\n" + "="*70)
    print("总结")
    print("="*70)
    print("""
从STEP文件导入后，PythonOCC提供了完整的CAD模型访问能力：

1. 完整的拓扑结构
   - 所有层级的拓扑元素（从COMPOUND到VERTEX）
   - 完整的父子关系和邻接关系
   - 任意两个拓扑元素之间的关联查询

2. 丰富的几何信息
   - 精确的3D坐标和参数化表示
   - 曲线和曲面的类型识别
   - 几何属性计算（长度、面积、法向量等）

3. 拓扑-几何关联
   - 每个拓扑元素都关联其底层几何表示
   - 可以在拓扑和几何之间自由切换

这些数据为后续的特征识别、分析和处理提供了完整的基础。
    """)

if __name__ == "__main__":
    main()