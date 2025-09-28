/**
 * 边选择和分析模块
 * 处理边的交互式选择和深度分析
 */

export class EdgeSelector {
    constructor(apiClient, renderer) {
        this.apiClient = apiClient;
        this.renderer = renderer;  // Three.js渲染器引用
        this.selectedEdges = [];
        this.edgeData = [];
        this.isSelectionMode = false;
        this.analysisResults = null;

        // 监听3D视图中的边选择变化
        document.addEventListener('edgeSelectionChanged', (e) => {
            this.selectedEdges = e.detail.selectedEdges;
            this.updateSelectionDisplay();
        });
    }

    async loadEdgesList() {
        try {
            const response = await fetch('/api/edges/list');
            const data = await response.json();

            if (data.success) {
                this.edgeData = data.edges;
                console.log(`加载了 ${data.total} 条边`);
                return data.edges;
            }
        } catch (error) {
            console.error('加载边列表失败:', error);
        }
        return [];
    }

    toggleSelectionMode() {
        this.isSelectionMode = !this.isSelectionMode;

        const btn = document.getElementById('toggleEdgeMode');
        const info = document.getElementById('edgeSelectionInfo');

        if (this.isSelectionMode) {
            btn.textContent = '退出边选择模式';
            btn.classList.add('active');
            info.style.display = 'block';

            // 让Three.js渲染器进入边选择模式
            if (this.renderer) {
                this.renderer.enterEdgeSelectionMode();
            }

            // 显示提示信息
            this.displaySelectionHint();
        } else {
            btn.textContent = '进入边选择模式';
            btn.classList.remove('active');
            info.style.display = 'none';

            // 让Three.js渲染器退出边选择模式
            if (this.renderer) {
                this.renderer.exitEdgeSelectionMode();
            }
        }

        return this.isSelectionMode;
    }

    displaySelectionHint() {
        const listContainer = document.getElementById('selectedEdgesList');
        listContainer.innerHTML = `
            <div class="hint" style="padding: 10px; background: #f0f9ff; border-radius: 4px;">
                <p><strong>边选择模式已激活</strong></p>
                <p>• 在3D视图中点击蓝色的边进行选择</p>
                <p>• 选中的边会变成紫色</p>
                <p>• 再次点击已选中的边可以取消选择</p>
                <p>• 选择完成后点击"分析选中的边"</p>
            </div>
            <div id="selectedEdgesInfo" style="margin-top: 10px;">
                <strong>已选择: </strong><span id="selectedCount">0</span> 条边
                <div id="selectedEdgesList" style="margin-top: 5px;"></div>
            </div>
        `;
    }

    updateSelectionDisplay() {
        // 更新选中边的数量
        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.textContent = this.selectedEdges.length;
        }

        // 显示选中的边ID列表
        const listElement = document.getElementById('selectedEdgesList');
        if (listElement && this.selectedEdges.length > 0) {
            listElement.innerHTML = this.selectedEdges.map(id =>
                `<span style="display: inline-block; margin: 2px; padding: 2px 6px; background: #ddd6fe; border-radius: 3px; font-size: 12px;">${id}</span>`
            ).join('');
        }

        // 更新导出按钮状态
        this.updateExportButtons();
    }

    updateSelectionUI() {
        const countSpan = document.getElementById('selectedCount');
        if (countSpan) {
            countSpan.textContent = this.selectedEdges.length;
        }

        // 显示选中的边ID列表
        const infoDiv = document.getElementById('selectedEdgesInfo');
        if (infoDiv && this.selectedEdges.length > 0) {
            const edgesList = this.selectedEdges.join(', ');
            infoDiv.innerHTML = `
                <strong>已选择: </strong><span id="selectedCount">${this.selectedEdges.length}</span> 条边
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    ${edgesList}
                </div>
            `;
        }
    }

    displayAvailableEdges(edges) {
        const listContainer = document.getElementById('selectedEdgesList');

        if (!edges || edges.length === 0) {
            listContainer.innerHTML = '<p class="hint">没有可选择的边</p>';
            return;
        }

        listContainer.innerHTML = '<p class="hint">可选择的边：</p>';

        edges.forEach(edge => {
            const edgeItem = document.createElement('div');
            edgeItem.className = 'edge-item';
            edgeItem.dataset.edgeId = edge.id;

            edgeItem.innerHTML = `
                <div>
                    <strong>${edge.id}</strong>
                    <span class="edge-info">${edge.type}, ${edge.length}mm</span>
                </div>
                <div class="edge-info">
                    邻接面: ${edge.faces}
                </div>
            `;

            edgeItem.addEventListener('click', () => {
                this.toggleEdgeSelection(edge.id, edgeItem);
            });

            listContainer.appendChild(edgeItem);
        });
    }

    toggleEdgeSelection(edgeId, element) {
        const index = this.selectedEdges.indexOf(edgeId);

        if (index === -1) {
            // 添加到选择列表
            this.selectedEdges.push(edgeId);
            element.classList.add('selected');
        } else {
            // 从选择列表移除
            this.selectedEdges.splice(index, 1);
            element.classList.remove('selected');
        }

        console.log('选中的边:', this.selectedEdges);

        // 更新导出按钮状态
        this.updateExportButtons();
    }

    clearSelection() {
        this.selectedEdges = [];

        // 清除Three.js中的选择
        if (this.renderer) {
            this.renderer.selectedEdges.clear();
            this.renderer.showAllEdges();  // 重置边的颜色
        }

        // 清除分析结果
        document.getElementById('edgeAnalysisResults').style.display = 'none';
        document.getElementById('edgeAnalysisResults').innerHTML = '';

        // 更新UI
        this.updateSelectionUI();
        this.updateExportButtons();
    }

    async analyzeSelectedEdges() {
        // 从Three.js渲染器获取选中的边
        if (this.renderer) {
            this.selectedEdges = this.renderer.getSelectedEdges();
        }

        if (this.selectedEdges.length === 0) {
            alert('请先在3D视图中选择要分析的边');
            return;
        }

        try {
            const response = await fetch('/api/edges/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    edge_ids: this.selectedEdges
                })
            });

            const data = await response.json();

            if (data.success) {
                this.analysisResults = data.analysis;
                this.displayAnalysisResults(data.analysis);
            } else {
                alert('分析失败: ' + (data.error || '未知错误'));
            }

        } catch (error) {
            console.error('边分析失败:', error);
            alert('边分析失败: ' + error.message);
        }
    }

    displayAnalysisResults(results) {
        const resultsContainer = document.getElementById('edgeAnalysisResults');
        resultsContainer.style.display = 'block';
        resultsContainer.innerHTML = '';

        results.forEach(result => {
            const detailDiv = document.createElement('div');
            detailDiv.className = 'edge-analysis-detail';

            detailDiv.innerHTML = `
                <h5>边 ${result.edge_id}</h5>

                <div class="analysis-section">
                    <h6>几何信息</h6>
                    <div class="analysis-data">
                        <div>类型: ${result.geometry.type}</div>
                        <div>长度: ${result.geometry.length.toFixed(6)} mm</div>
                        <div>参数范围: [${result.geometry.parameter_range.first.toFixed(3)}, ${result.geometry.parameter_range.last.toFixed(3)}]</div>
                        <div>是否闭合: ${result.geometry.is_closed ? '是' : '否'}</div>
                        <div>是否退化: ${result.geometry.is_degenerated ? '是' : '否'}</div>
                        ${this.formatPoints(result.geometry.points)}
                        ${this.formatCurvature(result.geometry.curvature)}
                        ${this.formatSpecificGeometry(result.geometry)}
                    </div>
                </div>

                <div class="analysis-section">
                    <h6>拓扑信息</h6>
                    <div class="analysis-data">
                        <div>邻接面数: ${result.topology.adjacent_face_count}</div>
                        <div>方向: ${result.topology.orientation}</div>
                        <div>是否缝合边: ${result.topology.is_seam ? '是' : '否'}</div>
                        <div>是否流形: ${result.topology.is_manifold ? '是' : '否'}</div>
                    </div>
                </div>

                <div class="analysis-section">
                    <h6>顶点信息</h6>
                    <div class="analysis-data">
                        ${this.formatVertices(result.vertices)}
                    </div>
                </div>

                <div class="analysis-section">
                    <h6>邻接面详细信息</h6>
                    <div class="analysis-data">
                        ${this.formatAdjacentFaces(result.adjacent_faces)}
                    </div>
                </div>

                <div class="analysis-section">
                    <h6>物理属性</h6>
                    <div class="analysis-data">
                        ${this.formatProperties(result.properties)}
                    </div>
                </div>

                <div class="analysis-section">
                    <h6>质量评估</h6>
                    <div class="analysis-data">
                        ${this.formatQuality(result.quality)}
                    </div>
                </div>
            `;

            resultsContainer.appendChild(detailDiv);
        });

        // 更新导出按钮
        this.updateExportButtons();
    }

    formatPoints(points) {
        return `
            <div>起点: [${points.start.map(p => p.toFixed(3)).join(', ')}]</div>
            <div>中点: [${points.middle.map(p => p.toFixed(3)).join(', ')}]</div>
            <div>终点: [${points.end.map(p => p.toFixed(3)).join(', ')}]</div>
        `;
    }

    formatCurvature(curvature) {
        if (curvature === null || curvature === undefined) {
            return '';
        }
        return `<div>曲率: ${curvature.toFixed(6)}</div>`;
    }

    formatSpecificGeometry(geometry) {
        let html = '';

        if (geometry.line_info) {
            html += `
                <div>直线原点: [${geometry.line_info.origin.map(p => p.toFixed(3)).join(', ')}]</div>
                <div>直线方向: [${geometry.line_info.direction.map(p => p.toFixed(3)).join(', ')}]</div>
            `;
        }

        if (geometry.circle_info) {
            html += `
                <div>圆心: [${geometry.circle_info.center.map(p => p.toFixed(3)).join(', ')}]</div>
                <div>半径: ${geometry.circle_info.radius.toFixed(3)} mm</div>
                <div>轴向: [${geometry.circle_info.axis.map(p => p.toFixed(3)).join(', ')}]</div>
            `;
        }

        return html;
    }

    formatVertices(vertices) {
        let html = `<div>顶点数: ${vertices.count}</div>`;

        if (vertices.start) {
            html += `<div>起始顶点: [${vertices.start.coordinates.map(c => c.toFixed(3)).join(', ')}]</div>`;
            html += `<div>起始顶点容差: ${vertices.start.tolerance.toExponential(3)}</div>`;
        }

        if (vertices.end && vertices.end !== vertices.start) {
            html += `<div>结束顶点: [${vertices.end.coordinates.map(c => c.toFixed(3)).join(', ')}]</div>`;
            html += `<div>结束顶点容差: ${vertices.end.tolerance.toExponential(3)}</div>`;
        }

        return html;
    }

    formatAdjacentFaces(faces) {
        if (!faces || faces.length === 0) {
            return '<div>无邻接面</div>';
        }

        let html = '';
        faces.forEach((face, index) => {
            html += `
                <div style="margin-bottom: 10px;">
                    <strong>面 ${index + 1}:</strong>
                    <div>类型: ${face.geometry.type}</div>
                    <div>面积: ${face.geometry.area.toFixed(3)} mm²</div>
                    <div>质心: [${face.geometry.centroid.map(c => c.toFixed(3)).join(', ')}]</div>
                    ${face.geometry.normal_at_center ?
                        `<div>法向量: [${face.geometry.normal_at_center.map(n => n.toFixed(3)).join(', ')}]</div>` : ''}
                    <div>边数: ${face.properties.edge_count}, 顶点数: ${face.properties.vertex_count}</div>
                </div>
            `;
        });

        return html;
    }

    formatProperties(props) {
        return `
            <div>容差: ${props.tolerance.toExponential(3)}</div>
            <div>线性质量: ${props.linear_mass.toFixed(6)}</div>
            ${props.centroid ?
                `<div>质心: [${props.centroid.map(c => c.toFixed(3)).join(', ')}]</div>` : ''}
            <div>包围盒对角线: ${props.bounding_box.diagonal.toFixed(3)} mm</div>
        `;
    }

    formatQuality(quality) {
        return `
            <div>是否为小边: ${quality.is_small_edge ? '是' : '否'}</div>
            <div>长度质量: ${quality.length_quality}</div>
            ${quality.curvature_variation ?
                `<div>曲率变化:
                    最小=${quality.curvature_variation.min.toFixed(6)},
                    最大=${quality.curvature_variation.max.toFixed(6)},
                    平均=${quality.curvature_variation.mean.toFixed(6)},
                    标准差=${quality.curvature_variation.std.toFixed(6)}
                </div>` : ''}
        `;
    }

    updateExportButtons() {
        const hasSelection = this.selectedEdges.length > 0;
        const hasAnalysis = this.analysisResults && this.analysisResults.length > 0;

        document.getElementById('exportEdgeJsonBtn').disabled = !hasAnalysis;
        document.getElementById('exportEdgeTxtBtn').disabled = !hasAnalysis;
    }

    async exportAnalysis(format) {
        if (!this.analysisResults || this.selectedEdges.length === 0) {
            alert('没有可导出的边分析结果');
            return;
        }

        try {
            const response = await fetch('/api/edges/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: format,
                    edge_ids: this.selectedEdges
                })
            });

            if (format === 'json') {
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], {
                    type: 'application/json'
                });
                this.downloadBlob(blob, `edge_analysis_${data.filename || 'export'}.json`);
            } else if (format === 'txt') {
                const blob = await response.blob();
                const filename = response.headers.get('content-disposition')
                    ?.split('filename=')[1] || 'edge_analysis.txt';
                this.downloadBlob(blob, filename);
            }

        } catch (error) {
            console.error('导出失败:', error);
            alert('导出失败: ' + error.message);
        }
    }

    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}