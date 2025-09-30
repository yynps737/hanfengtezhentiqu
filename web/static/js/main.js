/**
 * 主程序 - 极简版
 * 只处理文件上传和3D渲染
 */

import { ThreeRenderer } from './three-renderer.js';

class App {
    constructor() {
        // Three.js 渲染器
        this.renderer = null;

        // DOM 元素
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.clearBtn = document.getElementById('clearBtn');
        this.statusMessage = document.getElementById('statusMessage');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.resetViewBtn = document.getElementById('resetViewBtn');
        this.toggleWireframeBtn = document.getElementById('toggleWireframeBtn');
        this.toggleGridBtn = document.getElementById('toggleGridBtn');
        this.toggleAxesBtn = document.getElementById('toggleAxesBtn');

        this.init();
    }

    init() {
        console.log('[App] 开始初始化...');

        // 初始化 Three.js 渲染器
        this.renderer = new ThreeRenderer('three-container');

        // 绑定事件
        this.bindEvents();

        console.log('[App] 应用初始化完成');
    }

    bindEvents() {
        console.log('[App] 绑定事件...');

        // 点击上传区域
        this.uploadArea.addEventListener('click', () => {
            console.log('[App] 点击上传区域');
            this.fileInput.click();
        });

        // 文件选择
        this.fileInput.addEventListener('change', (e) => {
            console.log('[App] 文件选择事件触发');
            const file = e.target.files[0];
            if (file) {
                console.log('[App] 选择的文件:', file.name);
                this.handleFile(file);
            }
        });

        // 拖拽上传
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('drag-over');
        });

        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('drag-over');
        });

        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('drag-over');

            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFile(file);
            }
        });

        // 清除按钮
        this.clearBtn.addEventListener('click', () => {
            this.clearModel();
        });

        // 控制按钮
        this.resetViewBtn.addEventListener('click', () => {
            this.renderer.resetView();
        });

        this.toggleWireframeBtn.addEventListener('click', () => {
            this.renderer.toggleWireframe();
        });

        // 网格切换
        this.toggleGridBtn.addEventListener('click', () => {
            const visible = this.renderer.toggleGrid();
            this.toggleGridBtn.style.opacity = visible ? '1' : '0.5';
        });

        // 坐标轴切换
        this.toggleAxesBtn.addEventListener('click', () => {
            const visible = this.renderer.toggleAxes();
            this.toggleAxesBtn.style.opacity = visible ? '1' : '0.5';
        });
    }

    async handleFile(file) {
        console.log('[App] 处理文件:', file.name, file.size, 'bytes');

        // 检查文件类型
        const ext = file.name.split('.').pop().toLowerCase();
        console.log('[App] 文件扩展名:', ext);

        if (!['step', 'stp'].includes(ext)) {
            console.log('[App] 文件类型不支持');
            this.showStatus('请上传 STEP 或 STP 文件', 'error');
            return;
        }

        // 显示加载动画
        this.showLoading(true);
        this.showStatus('正在上传文件...', 'success');
        console.log('[App] 开始上传文件到服务器...');

        try {
            // 上传文件
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // 显示文件信息
                this.fileName.textContent = data.filename;
                this.fileInfo.classList.add('show');
                this.showStatus('文件上传成功！', 'success');

                // 渲染3D模型
                if (data.mesh) {
                    this.renderer.renderMesh(data.mesh);
                    this.showStatus('模型加载成功！', 'success');
                }
            } else {
                throw new Error(data.error || '上传失败');
            }

        } catch (error) {
            console.error('文件处理失败:', error);
            this.showStatus('错误: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async clearModel() {
        try {
            // 调用后端清除API
            await fetch('/api/clear', {
                method: 'POST'
            });

            // 清除前端显示
            this.fileInfo.classList.remove('show');
            this.fileName.textContent = '';
            this.fileInput.value = '';
            this.renderer.clearMesh();
            this.showStatus('模型已清除', 'success');

        } catch (error) {
            console.error('清除失败:', error);
            this.showStatus('清除失败: ' + error.message, 'error');
        }
    }

    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.add('show');
        } else {
            this.loadingOverlay.classList.remove('show');
        }
    }

    showStatus(message, type) {
        this.statusMessage.textContent = message;
        this.statusMessage.className = 'status-message show ' + type;

        // 3秒后自动隐藏
        setTimeout(() => {
            this.statusMessage.classList.remove('show');
        }, 3000);
    }
}

// 启动应用
window.addEventListener('DOMContentLoaded', () => {
    new App();
});