"""
焊缝检测模块
核心算法：识别不同类型的焊缝
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum

from .topology_analyzer import TopologyAnalyzer
from .geometry_calculator import GeometryCalculator


class WeldType(Enum):
    """焊缝类型枚举"""
    FILLET = "fillet"  # 角焊缝
    BUTT = "butt"      # 对接焊缝
    LAP = "lap"        # 搭接焊缝
    TSHAPE = "t-shape" # T型焊缝
    UNKNOWN = "unknown"


@dataclass
class WeldFeature:
    """焊缝特征数据类"""
    weld_type: WeldType
    edge_id: int
    face1_id: int
    face2_id: int
    angle: float
    length: float
    position: Tuple[float, float, float]
    is_linear: bool
    is_planar: bool
    confidence: float  # 识别置信度 0-1


class WeldDetector:
    """焊缝检测器"""

    def __init__(self):
        """初始化检测器"""
        # 焊缝判定参数（可调整）
        self.params = {
            'fillet': {
                'min_angle': 60,
                'max_angle': 120,
                'min_length': 5.0  # mm
            },
            'butt': {
                'min_angle': 150,
                'max_angle': 180,
                'min_length': 5.0,
                'max_gap': 5.0  # mm
            },
            'lap': {
                'max_angle': 30,  # 近平行
                'min_overlap': 10.0  # mm
            },
            't-shape': {
                'min_angle': 85,
                'max_angle': 95,
                'min_length': 5.0
            }
        }

        self.topology_analyzer = None
        self.detected_welds = []

    def detect_welds(self, shape) -> List[WeldFeature]:
        """
        检测形状中的所有焊缝

        Args:
            shape: TopoDS_Shape对象

        Returns:
            welds: 检测到的焊缝列表
        """
        print("\n开始焊缝检测...")

        # 初始化拓扑分析器
        self.topology_analyzer = TopologyAnalyzer(shape)

        # 统计拓扑元素
        counts = self.topology_analyzer.count_topology_elements()
        print(f"模型统计: {counts}")

        # 获取所有连接两个面的边
        edge_face_pairs = self.topology_analyzer.get_edges_with_two_faces()

        # 清空之前的结果
        self.detected_welds = []

        # 分析每条边
        for edge, face1, face2 in edge_face_pairs:
            weld = self._analyze_edge_for_weld(edge, face1, face2)
            if weld:
                self.detected_welds.append(weld)

        print(f"\n检测完成: 找到 {len(self.detected_welds)} 条焊缝")
        self._print_summary()

        return self.detected_welds

    def _analyze_edge_for_weld(self, edge, face1, face2) -> Optional[WeldFeature]:
        """
        分析单条边是否为焊缝

        Args:
            edge: 边
            face1: 第一个面
            face2: 第二个面

        Returns:
            weld: 焊缝特征或None
        """
        # 计算基本几何属性
        length = GeometryCalculator.calculate_edge_length(edge)
        angle = GeometryCalculator.calculate_dihedral_angle(edge, face1, face2)

        if angle is None:
            return None

        # 检查边和面的类型
        is_linear = GeometryCalculator.is_linear_edge(edge)
        is_planar = (
            GeometryCalculator.is_planar_face(face1) and
            GeometryCalculator.is_planar_face(face2)
        )

        # 获取边的中点位置
        midpoint = GeometryCalculator.get_edge_midpoint(edge)
        position = (midpoint.X(), midpoint.Y(), midpoint.Z())

        # 判断焊缝类型
        weld_type, confidence = self._classify_weld_type(
            angle, length, is_linear, is_planar
        )

        # 如果识别出焊缝类型
        if weld_type != WeldType.UNKNOWN:
            return WeldFeature(
                weld_type=weld_type,
                edge_id=id(edge),
                face1_id=id(face1),
                face2_id=id(face2),
                angle=angle,
                length=length,
                position=position,
                is_linear=is_linear,
                is_planar=is_planar,
                confidence=confidence
            )

        return None

    def _classify_weld_type(
        self, angle: float, length: float,
        is_linear: bool, is_planar: bool
    ) -> Tuple[WeldType, float]:
        """
        根据几何特征判断焊缝类型

        Args:
            angle: 二面角
            length: 边长度
            is_linear: 是否为直线边
            is_planar: 两个面是否都是平面

        Returns:
            (weld_type, confidence): 焊缝类型和置信度
        """
        # 角焊缝判定
        fillet_params = self.params['fillet']
        if (fillet_params['min_angle'] <= angle <= fillet_params['max_angle'] and
                length >= fillet_params['min_length'] and
                is_linear and is_planar):

            # 计算置信度（角度越接近90度越高）
            angle_diff = abs(90 - angle)
            confidence = max(0.5, 1.0 - angle_diff / 30)
            return WeldType.FILLET, confidence

        # T型焊缝判定（特殊的角焊缝，角度接近90度）
        tshape_params = self.params['t-shape']
        if (tshape_params['min_angle'] <= angle <= tshape_params['max_angle'] and
                length >= tshape_params['min_length'] and
                is_linear and is_planar):

            confidence = 0.9  # T型焊缝置信度较高
            return WeldType.TSHAPE, confidence

        # 对接焊缝判定
        butt_params = self.params['butt']
        if (butt_params['min_angle'] <= angle <= butt_params['max_angle'] and
                length >= butt_params['min_length']):

            # 计算置信度（角度越接近180度越高）
            angle_diff = abs(180 - angle)
            confidence = max(0.5, 1.0 - angle_diff / 30)
            return WeldType.BUTT, confidence

        # 搭接焊缝判定
        lap_params = self.params['lap']
        if angle <= lap_params['max_angle']:
            confidence = 0.6  # 搭接焊缝需要更多判定条件
            return WeldType.LAP, confidence

        return WeldType.UNKNOWN, 0.0

    def _print_summary(self):
        """打印检测结果摘要"""
        if not self.detected_welds:
            print("未检测到焊缝")
            return

        # 统计各类型焊缝
        type_counts = {}
        for weld in self.detected_welds:
            weld_type = weld.weld_type.value
            type_counts[weld_type] = type_counts.get(weld_type, 0) + 1

        print("\n焊缝类型统计:")
        for weld_type, count in type_counts.items():
            print(f"  {weld_type}: {count} 条")

        # 打印详细信息（前5条）
        print("\n焊缝详情（前5条）:")
        for i, weld in enumerate(self.detected_welds[:5], 1):
            print(f"  [{i}] {weld.weld_type.value}")
            print(f"      角度: {weld.angle:.2f}°")
            print(f"      长度: {weld.length:.2f}mm")
            print(f"      置信度: {weld.confidence:.2%}")

    def get_parameters(self) -> Dict:
        """获取当前检测参数"""
        return self.params

    def update_parameters(self, new_params: Dict):
        """更新检测参数"""
        for weld_type in new_params:
            if weld_type in self.params:
                self.params[weld_type].update(new_params[weld_type])
        print("检测参数已更新")

    def export_results(self) -> List[Dict]:
        """导出检测结果为字典格式（便于JSON序列化）"""
        results = []
        for weld in self.detected_welds:
            results.append({
                'type': weld.weld_type.value,
                'angle': round(weld.angle, 2),
                'length': round(weld.length, 2),
                'position': [round(x, 2) for x in weld.position],
                'is_linear': weld.is_linear,
                'is_planar': weld.is_planar,
                'confidence': round(weld.confidence, 3),
                'edge_id': str(weld.edge_id),
                'face1_id': str(weld.face1_id),
                'face2_id': str(weld.face2_id)
            })
        return results