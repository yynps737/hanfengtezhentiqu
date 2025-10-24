"""
应用入口
"""
import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 CAD模型查看器启动中...")
    print("=" * 50)
    print("📍 访问地址: http://localhost:5000")
    print("📋 API文档:")
    print("   - GET  /api/health       - 健康检查")
    print("   - POST /api/upload       - 上传STEP文件")
    print("   - POST /api/clear        - 清除会话")
    print("   - GET  /api/model/info   - 获取模型信息")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
