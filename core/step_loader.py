"""
STEP文件加载模块
"""

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
import os


class StepLoader:
    """STEP文件加载器"""

    def __init__(self):
        self.reader = None
        self.shape = None

    def load_file(self, filepath):
        """
        加载STEP文件

        Args:
            filepath: STEP文件路径

        Returns:
            shape: TopoDS_Shape对象
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        if not filepath.lower().endswith(('.step', '.stp')):
            raise ValueError("文件必须是STEP格式 (.step 或 .stp)")

        self.reader = STEPControl_Reader()
        status = self.reader.ReadFile(filepath)

        if status == IFSelect_RetDone:
            # 传输所有根
            self.reader.TransferRoots()
            # 获取形状
            self.shape = self.reader.OneShape()
            print(f"成功加载STEP文件: {filepath}")
            return self.shape
        else:
            raise Exception(f"加载STEP文件失败: {filepath}")

    def get_shape(self):
        """获取已加载的形状"""
        return self.shape

    def get_reader(self):
        """获取reader对象（用于高级操作）"""
        return self.reader