#!/usr/bin/env python
"""
焊缝检测研发平台启动脚本
"""

import os
import sys

# 添加项目路径
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

def main():
    """主函数"""
    print("=" * 50)
    print("焊缝特征提取研发平台")
    print("=" * 50)
    print()

    # 检查PythonOCC是否安装
    try:
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        print("✓ PythonOCC 已安装")
    except ImportError:
        print("✗ PythonOCC 未安装")
        print("请运行: conda install -c conda-forge pythonocc-core")
        sys.exit(1)

    # 检查Flask是否安装
    try:
        import flask
        print("✓ Flask 已安装")
    except ImportError:
        print("✗ Flask 未安装")
        print("请运行: conda env create -f environment.yml")
        print("然后: conda activate weld_research")
        sys.exit(1)

    print()
    print("启动服务器...")
    print("-" * 30)

    # 启动Flask应用
    from api.app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()