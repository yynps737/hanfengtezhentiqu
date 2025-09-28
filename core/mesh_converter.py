"""
网格转换模块
将OCCT形状转换为Three.js可用的网格数据
"""

from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.TopoDS import topods
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

        print(f"网格生成完成: {len(vertices)//3} 个顶点, {len(faces)//3} 个三角形")

        return {
            'vertices': vertices,
            'faces': faces
        }

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