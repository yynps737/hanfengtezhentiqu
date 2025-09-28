/**
 * API客户端模块
 * 处理与后端的所有通信
 */

const API_BASE = 'http://localhost:5000/api';

export class ApiClient {
    constructor() {
        this.currentFile = null;
    }

    async uploadFile(file) {
        if (!file) {
            throw new Error('未选择文件');
        }

        // 验证文件类型
        const validExtensions = ['.step', '.stp'];
        const fileExtension = file.name.toLowerCase().substr(file.name.lastIndexOf('.'));

        if (!validExtensions.includes(fileExtension)) {
            throw new Error('请选择STEP或STP文件');
        }

        // 验证文件大小
        if (file.size > 100 * 1024 * 1024) {
            throw new Error('文件过大，最大支持100MB');
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || '上传失败');
            }

            this.currentFile = file;
            return data;

        } catch (error) {
            console.error('文件上传失败:', error);
            throw error;
        }
    }

    async analyzeModel(parameters) {
        if (!this.currentFile) {
            throw new Error('请先上传STEP文件');
        }

        try {
            const response = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parameters })
            });

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // 如果成功但没有summary，提供默认值
            if (!data.summary) {
                data.summary = { total: 0, by_type: {} };
            }

            return data;

        } catch (error) {
            console.error('模型分析失败:', error);
            throw error;
        }
    }

    async getParameters() {
        try {
            const response = await fetch(`${API_BASE}/parameters`);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('获取参数失败:', error);
            return {
                min_angle: 70,
                max_angle: 110,
                min_joint_length: 10,
                optimal_angle: 90,
                min_plate_thickness: 1,
                max_plate_thickness: 50
            };
        }
    }

    async updateParameters(parameters) {
        try {
            const response = await fetch(`${API_BASE}/parameters`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(parameters)
            });

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || '参数更新失败');
            }

            return data;

        } catch (error) {
            console.error('参数更新失败:', error);
            throw error;
        }
    }

    async exportResults(format) {
        try {
            const response = await fetch(`${API_BASE}/export?format=${format}`);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            if (format === 'csv') {
                const blob = await response.blob();
                this.downloadBlob(blob, `welds_${this.currentFile.name}.csv`);
            } else {
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], {
                    type: 'application/json'
                });
                this.downloadBlob(blob, `welds_${this.currentFile.name}.json`);
            }

        } catch (error) {
            console.error('导出失败:', error);
            throw error;
        }
    }

    async clearSession() {
        try {
            const response = await fetch(`${API_BASE}/clear`, {
                method: 'POST'
            });

            this.currentFile = null;
            return response.ok;

        } catch (error) {
            console.error('清除会话失败:', error);
            return false;
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

    getCurrentFileName() {
        return this.currentFile ? this.currentFile.name : null;
    }

    hasCurrentFile() {
        return this.currentFile !== null;
    }
}