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

        // 边选择相关元素
        this.edgeSelectionPanel = document.getElementById('edgeSelectionPanel');
        this.toggleEdgeSelectionBtn = document.getElementById('toggleEdgeSelectionBtn');
        this.confirmEdgesBtn = document.getElementById('confirmEdgesBtn');
        this.exitEdgeSelectionBtn = document.getElementById('exitEdgeSelectionBtn');
        this.edgeSelectionInfo = document.getElementById('edgeSelectionInfo');

        // 边选择状态
        this.isEdgeSelectionMode = false;

        this.init();
    }

    init() {
        console.log('[App] 开始初始化...');

        // 初始化 Three.js 渲染器
        this.renderer = new ThreeRenderer('three-container');

        // 绑定事件
        this.bindEvents();

        // 监听边选择变化事件
        window.addEventListener('edgeSelectionChanged', (event) => {
            this.updateEdgeListUI(event.detail);
        });

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

        // 边选择按钮
        this.toggleEdgeSelectionBtn.addEventListener('click', () => {
            this.toggleEdgeSelectionMode();
        });

        this.confirmEdgesBtn.addEventListener('click', () => {
            this.confirmEdgeSelection();
        });

        this.exitEdgeSelectionBtn.addEventListener('click', () => {
            this.exitEdgeSelectionMode();
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

                // 渲染边
                if (data.edges) {
                    this.renderer.renderEdges(data.edges);
                    console.log(`[App] 加载 ${data.edges.length} 条边`);

                    // 显示边选择面板
                    this.edgeSelectionPanel.style.display = 'block';
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
            this.renderer.clearSelectedEdges();
            this.edgeSelectionPanel.style.display = 'none';
            this.isEdgeSelectionMode = false;
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

    updateEdgeListUI(detail) {
        const { selectedEdges, count } = detail;

        // 更新边选择信息显示
        if (count === 0) {
            this.edgeSelectionInfo.textContent = '未选择边';
            this.edgeSelectionInfo.style.color = '#999';
            this.confirmEdgesBtn.disabled = true;
        } else {
            this.edgeSelectionInfo.innerHTML = `
                <div style="font-weight: bold; color: #333;">已选择 ${count} 条边</div>
                ${selectedEdges.map(edge => `
                    <div style="margin-top: 5px; font-size: 12px;">边 ${edge.id}</div>
                `).join('')}
            `;
            this.confirmEdgesBtn.disabled = false;
        }
    }

    toggleEdgeSelectionMode() {
        this.isEdgeSelectionMode = !this.isEdgeSelectionMode;

        if (this.isEdgeSelectionMode) {
            // 开启选边模式
            this.renderer.setEdgeSelectionEnabled(true);
            this.toggleEdgeSelectionBtn.textContent = '停止选边';
            this.toggleEdgeSelectionBtn.classList.add('active');
            this.showStatus('选边模式已开启，点击边进行选择', 'success');
        } else {
            // 关闭选边模式
            this.renderer.setEdgeSelectionEnabled(false);
            this.toggleEdgeSelectionBtn.textContent = '开始选边';
            this.toggleEdgeSelectionBtn.classList.remove('active');
            this.showStatus('选边模式已关闭', 'success');
        }
    }

    confirmEdgeSelection() {
        const selectedEdges = this.renderer.getSelectedEdges();
        console.log('[App] 确定选择的边:', selectedEdges);
        this.showStatus(`已确定选择 ${selectedEdges.length} 条边`, 'success');
        // TODO: 这里可以添加后续处理逻辑
    }

    exitEdgeSelectionMode() {
        // 退出选边模式并清空选择
        this.isEdgeSelectionMode = false;
        this.renderer.setEdgeSelectionEnabled(false);
        this.renderer.clearSelectedEdges();
        this.toggleEdgeSelectionBtn.textContent = '开始选边';
        this.toggleEdgeSelectionBtn.classList.remove('active');
        this.showStatus('已退出选边模式', 'success');
    }
}

// 启动应用
window.addEventListener('DOMContentLoaded', () => {
    window.appInstance = new App();
});