"""
网格转换模块
将OCCT形状转换为Three.js可用的网格数据
"""

from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.TopoDS import topods
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GCPnts import GCPnts_UniformDeflection
import json


class MeshConverter:
    """将OCCT形状转换为Web可显示的网格"""

    @staticmethod
    def shape_to_mesh(shape, linear_deflection=0.5, angular_deflection=0.5):
        """
        将形状转换为三角网格

        Args:
            shape: TopoDS_Shape对象
            linear_deflection: 线性偏差（精度）
            angular_deflection: 角度偏差

        Returns:
            mesh_data: 包含顶点和面的字典
        """
        # 生成网格
        mesh = BRepMesh_IncrementalMesh(
            shape,
            linear_deflection,
            False,  # is_relative
            angular_deflection,
            True    # in_parallel
        )
        mesh.Perform()

        if not mesh.IsDone():
            raise Exception("网格生成失败")

        # 提取网格数据
        vertices = []
        faces = []

        # 遍历所有面
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        vertex_offset = 0

        while explorer.More():
            face = topods.Face(explorer.Current())

            # 获取面的三角化数据
            location = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation(face, location)

            if triangulation:
                # 获取顶点
                # 在PythonOCC中，直接遍历节点
                nb_nodes = triangulation.NbNodes()
                for i in range(1, nb_nodes + 1):
                    node = triangulation.Node(i)
                    # 应用变换
                    if not location.IsIdentity():
                        node.Transform(location.Transformation())
                    vertices.extend([node.X(), node.Y(), node.Z()])

                # 获取三角形索引
                nb_triangles = triangulation.NbTriangles()
                for i in range(1, nb_triangles + 1):
                    # 获取三角形的三个顶点索引
                    n1, n2, n3 = triangulation.Triangle(i).Get()
                    # 调整索引偏移（Three.js使用0基索引）
                    faces.extend([
                        vertex_offset + n1 - 1,
                        vertex_offset + n2 - 1,
                        vertex_offset + n3 - 1
                    ])

                vertex_offset += nb_nodes

            explorer.Next()

        # 提取边的线段数据（用于选择高亮）
        edges_data = MeshConverter.extract_edges(shape)

        print(f"网格生成完成: {len(vertices)//3} 个顶点, {len(faces)//3} 个三角形")

        return {
            'vertices': vertices,
            'faces': faces,
            'edges': edges_data
        }

    @staticmethod
    def extract_edges(shape):
        """
        提取边的线段数据用于3D显示和选择

        Args:
            shape: TopoDS_Shape对象

        Returns:
            edges_data: 边的线段数据列表
        """
        edges_data = []
        edge_idx = 0

        # 遍历所有边
        explorer = TopExp_Explorer(shape, TopAbs_EDGE)
        while explorer.More():
            edge = topods.Edge(explorer.Current())

            # 获取边的曲线
            curve = BRepAdaptor_Curve(edge)

            # 采样边上的点（用于绘制）
            points = []
            num_samples = 20  # 每条边采样20个点

            for i in range(num_samples):
                t = curve.FirstParameter() + \
                    (curve.LastParameter() - curve.FirstParameter()) * i / (num_samples - 1)
                pnt = curve.Value(t)
                points.extend([pnt.X(), pnt.Y(), pnt.Z()])

            edges_data.append({
                'id': f'EDGE_{edge_idx}',
                'points': points  # 用于绘制边的点序列
            })

            edge_idx += 1
            explorer.Next()

        return edges_data

    @staticmethod
    def shape_to_json(shape):
        """
        将形状转换为JSON格式

        Args:
            shape: TopoDS_Shape对象

        Returns:
            json_str: JSON字符串
        """
        mesh_data = MeshConverter.shape_to_mesh(shape)
        return json.dumps(mesh_data)