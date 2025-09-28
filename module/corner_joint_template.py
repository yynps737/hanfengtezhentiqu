"""
角接头特征模板
Corner Joint Feature Template

专门用于识别角接头（两个板件成一定角度连接的接头）
角接头特点：两个零件的边缘以一定角度相交，形成L型或V型结构
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
from enum import Enum
import numpy as np


class CornerJointType(Enum):
    """角接头子类型"""
    L_CORNER = "L型角接"      # 90度角接
    V_CORNER = "V型角接"      # 锐角或钝角角接
    T_CORNER = "T型角接"      # T型连接（一个板端部连接另一个板面）


@dataclass
class CornerJointParameters:
    """角接头识别参数"""
    # 角度约束（角接头的典型角度范围）
    min_angle: float = 70.0         # 最小角度
    max_angle: float = 110.0        # 最大角度
    optimal_angle: float = 90.0     # 最优角度（L型角接）

    # 边缘检测参数
    edge_distance_threshold: float = 2.0    # 边缘距离阈值(mm)
    edge_parallelism_angle: float = 5.0     # 平行度容差(度)

    # 尺寸约束
    min_joint_length: float = 10.0          # 最小接头长度(mm)
    min_plate_thickness: float = 1.0        # 最小板厚(mm)
    max_plate_thickness: float = 50.0       # 最大板厚(mm)

    # 几何约束
    require_planar_faces: bool = True       # 要求平面
    require_linear_edge: bool = True        # 要求直线边
    require_edge_proximity: bool = True     # 要求边缘接近

    # 容差
    angle_tolerance: float = 3.0            # 角度容差
    distance_tolerance: float = 0.5         # 距离容差


@dataclass
class CornerJointFeature:
    """角接头特征数据结构"""
    # 基本信息
    joint_type: CornerJointType            # 角接头类型
    joint_id: str                          # 唯一标识

    # 拓扑元素
    edge: object                           # 接头边(TopoDS_Edge)
    face1: object                          # 第一个板面(TopoDS_Face)
    face2: object                          # 第二个板面(TopoDS_Face)

    # 几何特征
    joint_angle: float                     # 接头角度(度)
    joint_length: float                    # 接头长度(mm)

    # 板材信息
    plate1_thickness: float                # 板1厚度(mm)
    plate2_thickness: float                # 板2厚度(mm)

    # 位置信息
    start_point: Tuple[float, float, float]    # 起点
    end_point: Tuple[float, float, float]      # 终点
    mid_point: Tuple[float, float, float]      # 中点
    joint_direction: Tuple[float, float, float] # 接头方向

    # 边缘信息
    is_edge_joint: bool                    # 是否为边缘接头
    edge_distance: float                   # 边缘距离(mm)

    # 评估
    confidence: float                      # 识别置信度(0-1)
    quality_score: float                   # 质量评分(0-100)

    # 可选字段（带默认值的放在最后）
    edge1_related: List[object] = None     # face1的相关边
    edge2_related: List[object] = None     # face2的相关边
    metadata: Dict = None                  # 额外信息


class CornerJointTemplate:
    """角接头特征模板类"""

    def __init__(self, parameters: Optional[CornerJointParameters] = None):
        """
        初始化角接头模板

        Args:
            parameters: 角接头参数
        """
        self.params = parameters or CornerJointParameters()
        self.detected_joints: List[CornerJointFeature] = []
        self.face_edge_map = {}  # 缓存面的边界边

    def match_edge(self, edge, face1, face2, topology_analyzer, geometry_calc) -> Optional[CornerJointFeature]:
        """
        检查边是否为角接头

        Args:
            edge: 候选边
            face1: 第一个面
            face2: 第二个面
            topology_analyzer: 拓扑分析器
            geometry_calc: 几何计算器

        Returns:
            如果是角接头返回特征，否则None
        """
        # 步骤1: 基本拓扑检查
        if not self._check_basic_topology(edge, face1, face2, geometry_calc):
            return None

        # 步骤2: 提取几何特征
        features = self._extract_geometry_features(edge, face1, face2, geometry_calc)
        if not features:
            return None

        # 步骤3: 检查是否为角接头（关键判断）
        if not self._is_corner_joint(edge, face1, face2, features, topology_analyzer):
            return None

        # 步骤4: 分类角接头类型
        joint_type = self._classify_corner_type(features)

        # 步骤5: 计算评估指标
        confidence = self._calculate_confidence(features)
        quality = self._calculate_quality(features)

        # 步骤6: 创建特征对象
        return self._create_feature(
            edge, face1, face2,
            features, joint_type,
            confidence, quality
        )

    def _check_basic_topology(self, edge, face1, face2, geometry_calc) -> bool:
        """基本拓扑检查"""
        # 检查直线边
        if self.params.require_linear_edge:
            if not geometry_calc.is_linear_edge(edge):
                return False

        # 检查平面
        if self.params.require_planar_faces:
            if not (geometry_calc.is_planar_face(face1) and
                    geometry_calc.is_planar_face(face2)):
                return False

        return True

    def _extract_geometry_features(self, edge, face1, face2, geometry_calc) -> Dict:
        """提取几何特征"""
        features = {}

        # 基本几何属性
        features['length'] = geometry_calc.calculate_edge_length(edge)
        angle = geometry_calc.calculate_dihedral_angle(edge, face1, face2)

        if angle is None:
            return None

        features['angle'] = angle

        # 位置信息
        midpoint = geometry_calc.get_edge_midpoint(edge)
        features['midpoint'] = (midpoint.X(), midpoint.Y(), midpoint.Z())

        # 检查长度
        if features['length'] < self.params.min_joint_length:
            return None

        # 检查角度范围（角接头的特征角度）
        if not (self.params.min_angle <= angle <= self.params.max_angle):
            return None

        return features

    def _is_corner_joint(self, edge, face1, face2, features, topology_analyzer) -> bool:
        """
        判断是否为角接头的核心逻辑
        角接头的关键特征：
        1. 两个面以一定角度相交
        2. 至少有一个面的边缘参与连接
        3. 连接边通常位于板的边缘位置
        """
        # 简化判断：对于角接头，主要看角度是否在合理范围内
        # 角接头的典型角度是70-110度
        angle = features.get('angle', 0)

        # 在指定角度范围内的都认为可能是角接头
        # 实际项目中可以加入更多判断条件
        if self.params.min_angle <= angle <= self.params.max_angle:
            return True

        return False

    def _get_face_edges(self, face, topology_analyzer):
        """获取面的所有边"""
        # 这里需要从拓扑分析器获取面的边
        # 简化处理，返回空列表
        # TODO: 实现获取面的边界边
        return []

    def _are_same_edge(self, edge1, edge2) -> bool:
        """判断两条边是否相同"""
        # 简单用id比较
        return id(edge1) == id(edge2)

    def _classify_corner_type(self, features) -> CornerJointType:
        """分类角接头类型"""
        angle = features['angle']

        # 根据角度分类
        if 85 <= angle <= 95:
            return CornerJointType.L_CORNER
        elif angle < 85:
            return CornerJointType.V_CORNER  # 锐角
        else:
            return CornerJointType.V_CORNER  # 钝角

    def _calculate_confidence(self, features) -> float:
        """计算识别置信度"""
        angle = features['angle']

        # 基于角度偏离最优值计算
        angle_deviation = abs(angle - self.params.optimal_angle)
        angle_score = max(0, 1 - angle_deviation / 30.0)

        # 基于长度的置信度
        length_score = min(1.0, features['length'] / 50.0)

        # 综合置信度
        confidence = 0.7 * angle_score + 0.3 * length_score

        return min(1.0, max(0.0, confidence))

    def _calculate_quality(self, features) -> float:
        """计算质量评分"""
        # 简化的质量评分
        base_score = 70.0

        # 角度接近90度加分
        angle = features['angle']
        if 85 <= angle <= 95:
            base_score += 20.0

        # 长度加分
        if features['length'] > 30:
            base_score += 10.0

        return min(100.0, base_score)

    def _create_feature(self, edge, face1, face2, features, joint_type,
                        confidence, quality) -> CornerJointFeature:
        """创建角接头特征对象"""
        import uuid

        return CornerJointFeature(
            joint_type=joint_type,
            joint_id=str(uuid.uuid4())[:8],
            edge=edge,
            face1=face1,
            face2=face2,
            joint_angle=features['angle'],
            joint_length=features['length'],
            plate1_thickness=5.0,  # TODO: 计算实际板厚
            plate2_thickness=5.0,  # TODO: 计算实际板厚
            start_point=(0, 0, 0),  # TODO: 获取实际坐标
            end_point=(0, 0, 0),    # TODO: 获取实际坐标
            mid_point=features['midpoint'],
            joint_direction=(0, 0, 1),  # TODO: 计算实际方向
            is_edge_joint=True,  # 简化处理
            edge_distance=0.0,
            confidence=confidence,
            quality_score=quality,
            metadata={}
        )

    def analyze_shape(self, shape, topology_analyzer, geometry_calc) -> List[CornerJointFeature]:
        """
        分析整个形状中的角接头

        Args:
            shape: TopoDS_Shape对象
            topology_analyzer: 拓扑分析器
            geometry_calc: 几何计算器

        Returns:
            检测到的角接头列表
        """
        self.detected_joints.clear()

        # 获取所有候选边
        edge_face_pairs = topology_analyzer.get_edges_with_two_faces()
        print(f"\n开始角接头分析: 共{len(edge_face_pairs)}条候选边")
        print(f"参数: 角度[{self.params.min_angle}-{self.params.max_angle}]°")

        # 检查每条边
        corner_count = 0
        for i, (edge, face1, face2) in enumerate(edge_face_pairs, 1):
            joint = self.match_edge(edge, face1, face2, topology_analyzer, geometry_calc)
            if joint:
                self.detected_joints.append(joint)
                corner_count += 1
                print(f"  边{i}: ✓ 角接头 ({joint.joint_type.value}, {joint.joint_angle:.1f}°)")

        print(f"\n分析完成: 找到{corner_count}个角接头")
        return self.detected_joints

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.detected_joints:
            return {'total': 0}

        stats = {
            'total': len(self.detected_joints),
            'by_type': {},
            'avg_angle': 0,
            'avg_confidence': 0,
            'total_length': 0
        }

        for joint in self.detected_joints:
            joint_type = joint.joint_type.value
            stats['by_type'][joint_type] = stats['by_type'].get(joint_type, 0) + 1
            stats['avg_angle'] += joint.joint_angle
            stats['avg_confidence'] += joint.confidence
            stats['total_length'] += joint.joint_length

        stats['avg_angle'] /= len(self.detected_joints)
        stats['avg_confidence'] /= len(self.detected_joints)

        return stats