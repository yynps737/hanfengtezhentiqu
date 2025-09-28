/**
 * 焊缝特征提取研发平台 - 主应用
 * 使用 Three.js r180 ES模块
 */

import { ThreeRenderer } from './three-renderer.js';
import { ApiClient } from './api-client.js';
import { UiManager } from './ui-manager.js';

class WeldDetectionApp {
    constructor() {
        this.renderer = null;
        this.apiClient = null;
        this.uiManager = null;
    }

    async init() {
        try {
            console.log('初始化焊缝检测应用...');

            // 初始化组件
            this.apiClient = new ApiClient();
            this.uiManager = new UiManager();

            // 初始化UI
            this.uiManager.init();

            // 初始化Three.js渲染器
            const container = document.getElementById('threejs-viewer');
            if (container) {
                this.renderer = new ThreeRenderer(container);
            } else {
                throw new Error('无法找到3D视图容器');
            }

            // 设置事件监听
            this.setupEventListeners();

            // 加载默认参数
            await this.loadDefaultParameters();

            // 设置全局函数（用于HTML onclick事件）
            this.setupGlobalFunctions();

            console.log('应用初始化完成');
            this.uiManager.showMessage('应用已就绪', 'success');

        } catch (error) {
            console.error('应用初始化失败:', error);
            this.uiManager?.showMessage(`初始化失败: ${error.message}`, 'error');
        }
    }

    setupEventListeners() {
        // 文件选择事件
        document.addEventListener('fileSelected', (e) => {
            this.handleFileUpload(e.detail.file);
        });

        // 分析按钮事件
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeModel();
        });

        // 导出按钮事件
        document.getElementById('exportJsonBtn').addEventListener('click', () => {
            this.exportResults('json');
        });

        document.getElementById('exportCsvBtn').addEventListener('click', () => {
            this.exportResults('csv');
        });

        // 轴向变化事件监听
        document.addEventListener('axisModeChanged', (e) => {
            this.uiManager.showMessage(`坐标系已切换至: ${e.detail.name}`, 'info');
        });
    }

    setupGlobalFunctions() {
        // 将函数绑定到全局作用域，用于HTML onclick事件
        window.updateParameters = () => this.updateParameters();
        window.clearFile = () => this.clearFile();
        window.resetView = () => this.resetView();
        window.toggleWireframe = () => this.toggleWireframe();
        window.toggleGrid = () => this.toggleGrid();
        window.toggleAxes = () => this.toggleAxes();
        window.switchAxisMode = () => this.switchAxisMode();
        window.openFullscreen = () => this.openFullscreen();
    }

    async handleFileUpload(file) {
        try {
            this.uiManager.showProgress('上传文件中...');

            const result = await this.apiClient.uploadFile(file);

            this.uiManager.showFileInfo(file.name);
            this.uiManager.setAnalyzeButtonEnabled(true);

            // 显示3D模型
            if (result.mesh) {
                this.renderer.displayMesh(result.mesh);
            }

            this.uiManager.showMessage('文件上传成功', 'success');

        } catch (error) {
            this.uiManager.showMessage(`上传失败: ${error.message}`, 'error');
        } finally {
            this.uiManager.hideProgress();
        }
    }

    async analyzeModel() {
        if (!this.apiClient.hasCurrentFile()) {
            this.uiManager.showMessage('请先上传STEP文件', 'error');
            return;
        }

        try {
            this.uiManager.showProgress('分析中...');

            const parameters = this.uiManager.getParameters();
            const result = await this.apiClient.analyzeModel(parameters);

            this.uiManager.displayResults(result);

            // 在3D视图中高亮焊缝
            if (result.welds && result.welds.length > 0) {
                this.renderer.highlightWelds(result.welds);
            }

            this.uiManager.showMessage(
                `分析完成: 找到 ${result.summary.total} 条焊缝`,
                'success'
            );

        } catch (error) {
            this.uiManager.showMessage(`分析失败: ${error.message}`, 'error');
        } finally {
            this.uiManager.hideProgress();
        }
    }

    async loadDefaultParameters() {
        try {
            const params = await this.apiClient.getParameters();
            this.uiManager.setParameters(params);
        } catch (error) {
            console.warn('加载默认参数失败:', error);
        }
    }

    async updateParameters() {
        try {
            const parameters = this.uiManager.getParameters();
            await this.apiClient.updateParameters(parameters);
            this.uiManager.showMessage('参数更新成功', 'success');
        } catch (error) {
            this.uiManager.showMessage(`参数更新失败: ${error.message}`, 'error');
        }
    }

    async exportResults(format) {
        if (!this.uiManager.getAnalysisResults()) {
            this.uiManager.showMessage('无结果可导出', 'error');
            return;
        }

        try {
            await this.apiClient.exportResults(format);
            this.uiManager.showMessage(`导出${format.toUpperCase()}成功`, 'success');
        } catch (error) {
            this.uiManager.showMessage(`导出失败: ${error.message}`, 'error');
        }
    }

    clearFile() {
        this.apiClient.clearSession();
        this.uiManager.clearFileInfo();
        this.uiManager.setAnalyzeButtonEnabled(false);

        // 清空3D视图的模型
        if (this.renderer && this.renderer.currentModel) {
            this.renderer.scene.remove(this.renderer.currentModel);
            this.renderer.currentModel = null;
        }

        this.uiManager.showMessage('文件已清除', 'info');
    }

    resetView() {
        if (this.renderer) {
            this.renderer.resetView();
        }
    }

    toggleWireframe() {
        if (this.renderer) {
            this.renderer.toggleWireframe();
        }
    }

    toggleGrid() {
        if (this.renderer) {
            this.renderer.toggleGrid();
        }
    }

    toggleAxes() {
        if (this.renderer) {
            this.renderer.toggleAxes();
        }
    }

    switchAxisMode() {
        if (this.renderer) {
            this.renderer.switchAxisMode();
        }
    }

    openFullscreen() {
        // 准备要传递的数据
        const modelData = {
            filename: this.apiClient.getCurrentFileName(),
            mesh: null,
            welds: null
        };

        // 获取当前模型数据
        if (this.renderer && this.renderer.currentModel) {
            const geometry = this.renderer.currentModel.geometry;
            if (geometry) {
                // 提取顶点数据
                const vertices = geometry.attributes.position.array;
                const indices = geometry.index ? geometry.index.array : null;

                modelData.mesh = {
                    vertices: Array.from(vertices),
                    faces: indices ? Array.from(indices) : []
                };
            }
        }

        // 获取焊缝数据
        const analysisResults = this.uiManager.getAnalysisResults();
        if (analysisResults && analysisResults.welds) {
            modelData.welds = analysisResults.welds;
        }

        // 将数据存储到sessionStorage
        sessionStorage.setItem('modelData', JSON.stringify(modelData));

        // 打开新窗口
        const fullscreenWindow = window.open(
            '/fullscreen.html',
            'fullscreen3D',
            'width=' + screen.width + ',height=' + screen.height + ',fullscreen=yes'
        );

        // 如果浏览器阻止弹窗，尝试在当前标签页打开
        if (!fullscreenWindow || fullscreenWindow.closed) {
            window.location.href = '/fullscreen.html';
        }
    }
}

// 应用启动
document.addEventListener('DOMContentLoaded', () => {
    const app = new WeldDetectionApp();
    app.init().catch(error => {
        console.error('应用启动失败:', error);
    });
});