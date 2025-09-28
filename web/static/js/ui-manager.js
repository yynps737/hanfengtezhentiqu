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
            min_angle: parseFloat(document.getElementById('min-angle').value),
            max_angle: parseFloat(document.getElementById('max-angle').value),
            optimal_angle: parseFloat(document.getElementById('optimal-angle').value),
            min_joint_length: parseFloat(document.getElementById('min-joint-length').value),
            min_plate_thickness: parseFloat(document.getElementById('min-plate-thickness').value),
            max_plate_thickness: parseFloat(document.getElementById('max-plate-thickness').value)
        };
    }

    setParameters(params) {
        document.getElementById('min-angle').value = params.min_angle || 70;
        document.getElementById('max-angle').value = params.max_angle || 110;
        document.getElementById('optimal-angle').value = params.optimal_angle || 90;
        document.getElementById('min-joint-length').value = params.min_joint_length || 10;
        document.getElementById('min-plate-thickness').value = params.min_plate_thickness || 1;
        document.getElementById('max-plate-thickness').value = params.max_plate_thickness || 50;
    }

    displayResults(data) {
        const resultsDiv = document.getElementById('results');
        this.analysisResults = data;

        // 清空之前的结果
        resultsDiv.innerHTML = '';

        // 显示摘要
        const byTypeHtml = data.summary.by_type ?
            Object.entries(data.summary.by_type).map(([type, count]) => `
                <div class="stat-item">
                    <div class="stat-value">${count}</div>
                    <div class="stat-label">${type}</div>
                </div>
            `).join('') : '';

        const summaryHtml = `
            <div class="result-summary">
                <h4>检测摘要</h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">${data.summary.total || 0}</div>
                        <div class="stat-label">总焊缝数</div>
                    </div>
                    ${byTypeHtml}
                </div>
            </div>
        `;
        resultsDiv.innerHTML = summaryHtml;

        // 显示详细列表
        if (data.welds && data.welds.length > 0) {
            const weldsHtml = data.welds.map((weld, index) => `
                <div class="result-item fillet">
                    <div class="result-header">
                        <span class="result-type">${weld.subtype}</span>
                        <span class="result-confidence">${(weld.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="result-details">
                        <div>ID: ${weld.id}</div>
                        <div>角度: ${weld.angle.toFixed(2)}°</div>
                        <div>长度: ${weld.length.toFixed(2)}mm</div>
                        <div>板厚: ${weld.plate1_thickness ? weld.plate1_thickness.toFixed(1) : '-'}×${weld.plate2_thickness ? weld.plate2_thickness.toFixed(1) : '-'}mm</div>
                        <div>质量评分: ${weld.quality_score}/100</div>
                        <div>位置: ${weld.position.map(p => p.toFixed(1)).join(', ')}</div>
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
            'corner': '角接头',
            'L_CORNER': 'L型角接',
            'V_CORNER': 'V型角接',
            'T_CORNER': 'T型角接'
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