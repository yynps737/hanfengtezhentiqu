"""
会话管理服务

新架构说明：
- 保存完整几何数据（geometry_data）
- 保存映射字典（vertices_map, edges_map, faces_map）用于回溯 OCC 对象
- 可选保存网格数据（mesh）用于快速预览
"""


class SessionService:
    """
    会话管理服务
    
    注意：当前使用全局变量存储单用户会话
    多用户场景需要改用 Flask-Session 或数据库
    """
    
    # 全局会话存储（单用户）
    _current_model = {
        'shape': None,              # TopoDS_Shape 对象
        'geometry_data': None,      # 完整几何数据（新架构）
        'vertices_map': {},         # hash -> TopoDS_Vertex
        'edges_map': {},            # hash -> TopoDS_Edge（用于焊缝回溯）
        'faces_map': {},            # hash -> TopoDS_Face
        'mesh': None,               # 可选的三角网格（用于预览）
        'filename': None            # 文件名
    }
    
    @classmethod
    def save_model(cls, shape, geometry_data=None, edges_map=None, 
                   faces_map=None, vertices_map=None, mesh=None, filename=None):
        """
        保存模型到会话（新架构）
        
        Args:
            shape: TopoDS_Shape 对象
            geometry_data: 完整几何数据（新架构）
            edges_map: 边哈希映射（用于焊缝回溯）
            faces_map: 面哈希映射
            vertices_map: 顶点哈希映射
            mesh: 可选的网格数据
            filename: 文件名
        """
        cls._current_model['shape'] = shape
        cls._current_model['geometry_data'] = geometry_data
        cls._current_model['edges_map'] = edges_map or {}
        cls._current_model['faces_map'] = faces_map or {}
        cls._current_model['vertices_map'] = vertices_map or {}
        cls._current_model['mesh'] = mesh
        cls._current_model['filename'] = filename
    
    @classmethod
    def get_model(cls):
        """
        获取当前会话的模型
        
        Returns:
            dict: 模型数据
        """
        return cls._current_model
    
    @classmethod
    def get_shape(cls):
        """
        获取 TopoDS_Shape 对象
        
        Returns:
            TopoDS_Shape: 形状对象
        """
        return cls._current_model['shape']
    
    @classmethod
    def get_geometry_data(cls):
        """
        获取完整几何数据
        
        Returns:
            dict: 几何数据
        """
        return cls._current_model['geometry_data']
    
    @classmethod
    def get_edges_map(cls):
        """
        获取边映射（用于焊缝回溯）
        
        Returns:
            dict: 边映射
        """
        return cls._current_model['edges_map']
    
    @classmethod
    def get_faces_map(cls):
        """
        获取面映射
        
        Returns:
            dict: 面映射
        """
        return cls._current_model['faces_map']
    
    @classmethod
    def get_edge_by_hash(cls, edge_hash):
        """
        根据哈希值获取边对象（用于焊缝选择）
        
        Args:
            edge_hash: 边哈希值
            
        Returns:
            TopoDS_Edge: 边对象，如果不存在返回 None
        """
        return cls._current_model['edges_map'].get(edge_hash)
    
    @classmethod
    def get_face_by_hash(cls, face_hash):
        """
        根据哈希值获取面对象
        
        Args:
            face_hash: 面哈希值
            
        Returns:
            TopoDS_Face: 面对象，如果不存在返回 None
        """
        return cls._current_model['faces_map'].get(face_hash)
    
    @classmethod
    def clear_model(cls):
        """清除当前会话的模型"""
        cls._current_model['shape'] = None
        cls._current_model['geometry_data'] = None
        cls._current_model['vertices_map'] = {}
        cls._current_model['edges_map'] = {}
        cls._current_model['faces_map'] = {}
        cls._current_model['mesh'] = None
        cls._current_model['filename'] = None
    
    @classmethod
    def has_model(cls):
        """
        检查是否有加载的模型
        
        Returns:
            bool: 是否有模型
        """
        return cls._current_model['shape'] is not None

