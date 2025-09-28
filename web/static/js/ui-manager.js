/**
 * UI管理模块
 * 处理所有用户界面交互
 */

export class UiManager {
    constructor() {
        this.isAnalyzing = false;
        this.analysisResults = null;
    }

    init() {
        this.setupFileUpload();
        console.log('UI管理器初始化完成');
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        // 点击上传
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });
    }

    handleFileSelect(file) {
        // 发出文件选择事件
        const event = new CustomEvent('fileSelected', { detail: { file } });
        document.dispatchEvent(event);
    }

    showFileInfo(filename) {
        document.getElementById('fileName').textContent = filename;
        document.getElementById('fileInfo').style.display = 'block';
        document.getElementById('uploadArea').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
    }

    clearFileInfo() {
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('uploadArea').style.display = 'block';
        document.getElementById('fileInput').value = '';
        document.getElementById('analyzeBtn').disabled = true;
        this.clearResults();
    }

    getParameters() {
        return {
            fillet: {
                min_angle: parseFloat(document.getElementById('fillet-min-angle').value),
                max_angle: parseFloat(document.getElementById('fillet-max-angle').value),
                min_length: parseFloat(document.getElementById('fillet-min-length').value)
            },
            butt: {
                min_angle: parseFloat(document.getElementById('butt-min-angle').value),
                max_angle: parseFloat(document.getElementById('butt-max-angle').value)
            }
        };
    }

    setParameters(params) {
        if (params.fillet) {
            document.getElementById('fillet-min-angle').value = params.fillet.min_angle || 60;
            document.getElementById('fillet-max-angle').value = params.fillet.max_angle || 120;
            document.getElementById('fillet-min-length').value = params.fillet.min_length || 5;
        }

        if (params.butt) {
            document.getElementById('butt-min-angle').value = params.butt.min_angle || 150;
            document.getElementById('butt-max-angle').value = params.butt.max_angle || 180;
        }
    }

    displayResults(data) {
        const resultsDiv = document.getElementById('results');
        this.analysisResults = data;

        // 清空之前的结果
        resultsDiv.innerHTML = '';

        // 显示摘要
        const summaryHtml = `
            <div class="result-summary">
                <h4>检测摘要</h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">${data.summary.total}</div>
                        <div class="stat-label">总焊缝数</div>
                    </div>
                    ${Object.entries(data.summary.by_type).map(([type, count]) => `
                        <div class="stat-item">
                            <div class="stat-value">${count}</div>
                            <div class="stat-label">${this.getWeldTypeName(type)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        resultsDiv.innerHTML = summaryHtml;

        // 显示详细列表
        if (data.welds && data.welds.length > 0) {
            const weldsHtml = data.welds.map((weld, index) => `
                <div class="result-item ${weld.type}">
                    <div class="result-header">
                        <span class="result-type">${this.getWeldTypeName(weld.type)}</span>
                        <span class="result-confidence">${(weld.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="result-details">
                        <div>角度: ${weld.angle.toFixed(2)}°</div>
                        <div>长度: ${weld.length.toFixed(2)}mm</div>
                        <div>位置: ${weld.position.map(p => p.toFixed(1)).join(', ')}</div>
                        <div>类型: ${weld.is_linear ? '直线' : '曲线'}</div>
                    </div>
                </div>
            `).join('');

            resultsDiv.innerHTML += weldsHtml;
        }

        // 启用导出按钮
        document.getElementById('exportJsonBtn').disabled = false;
        document.getElementById('exportCsvBtn').disabled = false;
    }

    clearResults() {
        document.getElementById('results').innerHTML = `
            <div class="no-results">
                <p>暂无分析结果</p>
            </div>
        `;

        document.getElementById('exportJsonBtn').disabled = true;
        document.getElementById('exportCsvBtn').disabled = true;

        this.analysisResults = null;
    }

    showMessage(message, type = 'info') {
        const status = document.getElementById('status');
        status.textContent = message;
        status.className = `status-${type}`;

        // 3秒后恢复
        setTimeout(() => {
            status.textContent = '就绪';
            status.className = '';
        }, 3000);
    }

    showProgress(message) {
        document.getElementById('status').style.display = 'none';
        document.getElementById('progress').style.display = 'inline-block';
        document.getElementById('progress').querySelector('span:last-child').textContent = message;
        this.isAnalyzing = true;
    }

    hideProgress() {
        document.getElementById('status').style.display = 'inline';
        document.getElementById('progress').style.display = 'none';
        this.isAnalyzing = false;
    }

    getWeldTypeName(type) {
        const names = {
            'fillet': '角焊缝',
            'butt': '对接焊缝',
            'lap': '搭接焊缝',
            't-shape': 'T型焊缝'
        };
        return names[type] || type;
    }

    setAnalyzeButtonEnabled(enabled) {
        const btn = document.getElementById('analyzeBtn');
        btn.disabled = !enabled;
        if (enabled && !this.isAnalyzing) {
            btn.textContent = '🔍 开始分析';
        } else {
            btn.textContent = this.isAnalyzing ? '分析中...' : '🔍 开始分析';
        }
    }

    getAnalysisResults() {
        return this.analysisResults;
    }
}