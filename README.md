# 焊缝特征提取研发平台

## 项目简介

这是一个基于 OpenCASCADE (OCCT) 的焊缝特征自动提取算法研发平台，用于验证从 STEP 模型中自动识别焊缝的可行性。

## 功能特性

- 🔧 **STEP文件解析**：支持标准STEP格式的3D模型导入
- 🔍 **自动特征识别**：自动识别角焊缝、对接焊缝等多种焊缝类型
- 📊 **参数可调**：支持调整识别算法的各项参数
- 🎨 **3D可视化**：基于Three.js的3D模型显示和焊缝高亮
- 💾 **结果导出**：支持JSON和CSV格式的结果导出

## 目录结构

```
weld_research/
├── core/               # 核心算法模块
│   ├── step_loader.py      # STEP文件加载
│   ├── topology_analyzer.py # 拓扑分析
│   ├── geometry_calculator.py # 几何计算
│   └── weld_detector.py    # 焊缝检测
├── api/                # Flask API后端
│   └── app.py              # API接口实现
├── web/                # 前端界面
│   ├── index.html          # 主页面
│   └── static/
│       ├── css/            # 样式文件
│       └── js/             # JavaScript脚本
├── test_data/          # 测试STEP文件
├── requirements.txt    # Python依赖
├── run.py             # 启动脚本
└── README.md          # 本文档
```

## 安装指南

### 1. 环境要求

- Python 3.10+
- Conda (推荐) 或 pip

### 2. 安装PythonOCC

使用 conda 安装（推荐）：
```bash
conda create -n weld_research python=3.10
conda activate weld_research
conda install -c conda-forge pythonocc-core
```

### 3. 使用environment.yml安装所有依赖（推荐）

```bash
conda env create -f environment.yml
conda activate weld_research
```

或者手动安装：
```bash
conda install -c conda-forge pythonocc-core
pip install flask flask-cors numpy werkzeug
```

## 快速开始

### 1. 启动服务

```bash
python run.py
```

或直接运行：
```bash
cd weld_research
python api/app.py
```

### 2. 访问界面

打开浏览器访问：http://localhost:5000

### 3. 使用流程

1. **上传文件**：选择或拖拽STEP文件到上传区
2. **调整参数**：根据需要调整检测参数
3. **开始分析**：点击"开始分析"按钮
4. **查看结果**：在右侧面板查看检测结果
5. **导出数据**：选择JSON或CSV格式导出

## API接口文档

### 上传文件
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (STEP文件)
```

### 分析模型
```
POST /api/analyze
Content-Type: application/json
Body: {
    "parameters": {
        "fillet": {"min_angle": 60, "max_angle": 120},
        "butt": {"min_angle": 150, "max_angle": 180}
    }
}
```

### 获取参数
```
GET /api/parameters
```

### 导出结果
```
GET /api/export?format=json
GET /api/export?format=csv
```

## 焊缝类型说明

### 角焊缝 (Fillet Weld)
- 角度范围：60° - 120°
- 两个面通过一条边连接
- 适用于T型连接

### 对接焊缝 (Butt Weld)
- 角度范围：150° - 180°
- 两个面近似平行
- 适用于板材对接

### 搭接焊缝 (Lap Weld)
- 角度范围：< 30°
- 两个面重叠
- 适用于搭接连接

## 核心算法说明

1. **拓扑分析**：使用 `TopExp::MapShapesAndAncestors` 构建边-面映射关系
2. **几何计算**：计算二面角、边长度等几何属性
3. **特征匹配**：根据几何特征匹配焊缝模板
4. **置信度评估**：基于特征符合程度计算识别置信度

## 开发指南

### 添加新的焊缝类型

在 `core/weld_detector.py` 中：

```python
# 1. 在 WeldType 枚举中添加新类型
class WeldType(Enum):
    NEW_TYPE = "new_type"

# 2. 在 __init__ 中添加参数
self.params['new_type'] = {
    'min_angle': 45,
    'max_angle': 90,
    'min_length': 10.0
}

# 3. 在 _classify_weld_type 中添加判定逻辑
```

### 自定义几何计算

在 `core/geometry_calculator.py` 中添加新的静态方法：

```python
@staticmethod
def calculate_custom_feature(edge, face1, face2):
    """自定义特征计算"""
    # 实现计算逻辑
    return feature_value
```

## 常见问题

### Q: PythonOCC安装失败
A: 建议使用conda安装，确保Python版本为3.10

### Q: 文件上传失败
A: 检查文件格式是否为STEP/STP，文件大小不超过100MB

### Q: 分析结果不准确
A: 尝试调整检测参数，特别是角度范围和最小长度

## 后续计划

- [ ] 添加更多焊缝类型识别
- [ ] 支持批量文件处理
- [ ] 增强3D可视化（显示实际模型）
- [ ] 添加焊接路径优化算法
- [ ] 集成机器学习优化识别

## 许可证

本项目仅供研发使用

## 联系方式

如有问题或建议，请联系开发团队。