/**
 * Three.js 渲染器 - 极简版
 * 只负责渲染从后端OCC获取的网格数据
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class ThreeRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentMesh = null;  // 当前显示的模型
        this.isWireframe = false;

        // 辅助对象
        this.grid = null;
        this.axes = null;
        this.isGridVisible = true;
        this.isAxesVisible = true;

        // 边选择相关
        this.edgesGroup = null;           // 所有边的容器（线段）
        this.selectedEdgesGroup = null;   // 已选边的容器（圆柱体）
        this.edgesData = [];              // 边数据数组
        this.selectedEdges = new Set();   // 已选中边的ID集合
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.edgeSelectionEnabled = false; // 选边模式开关
        this.hoveredEdgeId = null;        // 当前悬停的边ID

        this.init();
        this.setupEdgeSelection();
    }

    init() {
        // 创建场景 - 渐变背景（专业CAD风格）
        this.scene = new THREE.Scene();

        // 创建渐变背景（上浅下深）
        const canvas = document.createElement('canvas');
        canvas.width = 2;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 512);
        gradient.addColorStop(0, '#e8eaf6');    // 顶部：浅蓝灰
        gradient.addColorStop(0.5, '#b0bec5');  // 中部：中灰蓝
        gradient.addColorStop(1, '#546e7a');    // 底部：深蓝灰
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 2, 512);

        const texture = new THREE.CanvasTexture(canvas);
        this.scene.background = texture;

        // 创建相机 - CAD模式：Z轴朝上
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
        this.camera.position.set(200, 200, 200);
        this.camera.up.set(0, 0, 1);  // Z轴朝上（CAD标准坐标系）

        // 创建渲染器 - 物理正确的渲染
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;  // 正确的颜色空间
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;  // 电影级色调映射
        this.renderer.toneMappingExposure = 1.0;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        // 添加轨道控制器
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // 添加光源
        this.setupLights();

        // 添加网格和坐标轴
        this.setupHelpers();

        // 开始渲染循环
        this.animate();

        // 响应窗口大小变化
        window.addEventListener('resize', () => this.onWindowResize());

        console.log('Three.js 渲染器初始化完成');
    }

    setupLights() {
        // 环境光 - 柔和的基础照明
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambient);

        // 主方向光 - 模拟太阳光
        const mainLight = new THREE.DirectionalLight(0xffffff, 1.0);
        mainLight.position.set(100, 100, 150);
        mainLight.castShadow = true;
        this.scene.add(mainLight);

        // 补充光 - 从下方照亮暗部
        const fillLight = new THREE.DirectionalLight(0xb3c5d7, 0.3);
        fillLight.position.set(-50, -50, -50);
        this.scene.add(fillLight);

        // 半球光 - 模拟天空和地面的环境光
        const hemiLight = new THREE.HemisphereLight(0xddeeff, 0x444444, 0.4);
        this.scene.add(hemiLight);
    }

    setupHelpers() {
        // 网格 - 在XY平面（Z=0），淡雅风格
        this.grid = new THREE.GridHelper(200, 20, 0x90a4ae, 0xcfd8dc);
        this.grid.rotation.x = Math.PI / 2;  // 旋转到XY平面，使Z轴垂直
        this.grid.material.opacity = 0.3;
        this.grid.material.transparent = true;
        this.grid.visible = this.isGridVisible;
        this.scene.add(this.grid);

        // 坐标轴 - X红色, Y绿色, Z蓝色（向上）
        this.axes = new THREE.AxesHelper(100);
        this.axes.visible = this.isAxesVisible;
        this.scene.add(this.axes);
    }

    /**
     * 渲染从后端获取的网格数据
     * @param {Object} meshData - 来自后端OCC的网格数据
     */
    renderMesh(meshData) {
        // 清除旧模型
        this.clearMesh();

        if (!meshData || !meshData.vertices || !meshData.indices) {
            console.error('无效的网格数据');
            return;
        }

        console.log('开始渲染网格:', {
            vertices: meshData.vertices.length / 3,
            faces: meshData.indices.length / 3
        });

        // 创建几何体
        const geometry = new THREE.BufferGeometry();

        // 设置顶点
        const vertices = new Float32Array(meshData.vertices);
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

        // 设置索引
        const indices = new Uint32Array(meshData.indices);
        geometry.setIndex(new THREE.BufferAttribute(indices, 1));

        // 计算法线
        geometry.computeVertexNormals();

        // 创建金属质感材质（专业CAD风格）
        const material = new THREE.MeshStandardMaterial({
            color: 0xc8d6e5,        // 浅灰蓝色（金属基色）
            metalness: 0.6,          // 金属度
            roughness: 0.3,          // 粗糙度（越小越光滑）
            envMapIntensity: 1.0,    // 环境贴图强度
            side: THREE.DoubleSide,
            flatShading: false
        });

        // 创建网格
        this.currentMesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.currentMesh);

        // 自动调整视角
        this.fitCameraToModel();

        console.log('网格渲染完成');
    }

    /**
     * 自动调整相机以适应模型
     */
    fitCameraToModel() {
        if (!this.currentMesh) return;

        // 计算包围盒
        const box = new THREE.Box3().setFromObject(this.currentMesh);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        // 计算合适的相机距离
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = this.camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / Math.tan(fov / 2));
        cameraZ *= 1.5; // 增加一些边距

        // 设置相机位置
        this.camera.position.set(
            center.x + cameraZ,
            center.y + cameraZ,
            center.z + cameraZ
        );

        // 设置控制器目标
        this.controls.target.copy(center);
        this.controls.update();
    }

    /**
     * 清除当前模型
     */
    clearMesh() {
        if (this.currentMesh) {
            this.scene.remove(this.currentMesh);
            this.currentMesh.geometry.dispose();
            this.currentMesh.material.dispose();
            this.currentMesh = null;
            console.log('模型已清除');
        }
    }

    /**
     * 重置视角
     */
    resetView() {
        if (this.currentMesh) {
            this.fitCameraToModel();
        } else {
            this.camera.position.set(200, 200, 200);
            this.controls.target.set(0, 0, 0);
            this.controls.update();
        }
    }

    /**
     * 切换线框模式
     */
    toggleWireframe() {
        if (!this.currentMesh) return;

        this.isWireframe = !this.isWireframe;
        this.currentMesh.material.wireframe = this.isWireframe;

        console.log('线框模式:', this.isWireframe ? '开启' : '关闭');
    }

    /**
     * 切换网格显示
     */
    toggleGrid() {
        if (!this.grid) return;

        this.isGridVisible = !this.isGridVisible;
        this.grid.visible = this.isGridVisible;

        console.log('网格显示:', this.isGridVisible ? '开启' : '关闭');
        return this.isGridVisible;
    }

    /**
     * 切换坐标轴显示
     */
    toggleAxes() {
        if (!this.axes) return;

        this.isAxesVisible = !this.isAxesVisible;
        this.axes.visible = this.isAxesVisible;

        console.log('坐标轴显示:', this.isAxesVisible ? '开启' : '关闭');
        return this.isAxesVisible;
    }

    /**
     * 渲染循环
     */
    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    /**
     * 窗口大小调整
     */
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    /**
     * 设置边选择功能
     */
    setupEdgeSelection() {
        // 监听鼠标点击事件
        this.container.addEventListener('click', (event) => this.onEdgeClick(event));

        // 监听鼠标移动事件（悬停高亮）
        this.container.addEventListener('mousemove', (event) => this.onEdgeHover(event));
    }

    /**
     * 渲染边
     */
    renderEdges(edgesData) {
        // 清除旧边
        if (this.edgesGroup) {
            this.scene.remove(this.edgesGroup);
            this.edgesGroup.traverse((obj) => {
                if (obj.geometry) obj.geometry.dispose();
                if (obj.material) obj.material.dispose();
            });
        }

        if (this.selectedEdgesGroup) {
            this.scene.remove(this.selectedEdgesGroup);
            this.selectedEdgesGroup.traverse((obj) => {
                if (obj.geometry) obj.geometry.dispose();
                if (obj.material) obj.material.dispose();
            });
        }

        this.edgesData = edgesData;
        this.edgesGroup = new THREE.Group();
        this.edgesGroup.name = 'edges';

        this.selectedEdgesGroup = new THREE.Group();
        this.selectedEdgesGroup.name = 'selectedEdges';

        // 为每条边创建线段
        edgesData.forEach(edge => {
            const geometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(...edge.start),
                new THREE.Vector3(...edge.end)
            ]);

            const material = new THREE.LineBasicMaterial({
                color: 0x000000,      // 黑色边线
                linewidth: 2,
                opacity: 0.6,
                transparent: true
            });

            const line = new THREE.Line(geometry, material);
            line.userData.edgeId = edge.id;     // 存储显示用ID
            line.userData.edgeHash = edge.hash;  // 存储OCC永久标识符
            line.userData.edgeData = edge;       // 存储完整边数据
            this.edgesGroup.add(line);
        });

        this.scene.add(this.edgesGroup);
        this.scene.add(this.selectedEdgesGroup);
        console.log(`渲染边: ${edgesData.length} 条`);
    }

    /**
     * 鼠标悬停边（高亮效果）- 重写版本，修复黄色残留问题
     */
    onEdgeHover(event) {
        // 只有在开启选边模式时才响应悬停
        if (!this.edgesGroup || !this.edgeSelectionEnabled) {
            // 恢复默认光标
            this.container.style.cursor = 'default';
            this.clearHoverEffect();
            return;
        }

        // 计算鼠标位置
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        // 射线检测（缩小拾取范围）
        this.raycaster.setFromCamera(this.mouse, this.camera);
        this.raycaster.params.Line.threshold = 2;  // 2像素容差

        const intersects = this.raycaster.intersectObjects(this.edgesGroup.children, false);

        if (intersects.length > 0) {
            const hoveredLine = intersects[0].object;
            const edgeId = hoveredLine.userData.edgeId;

            // 忽略已选中的边（已经隐藏或变成圆柱体）
            if (this.selectedEdges.has(edgeId)) {
                this.container.style.cursor = 'default';
                this.clearHoverEffect();
                return;
            }

            // 如果悬停在新的边上
            if (edgeId !== this.hoveredEdgeId) {
                this.clearHoverEffect();
                this.hoveredEdgeId = edgeId;

                // 应用悬停高亮效果
                hoveredLine.material.color.setHex(0xffeb3b);  // 黄色高亮
                hoveredLine.material.opacity = 1.0;
                hoveredLine.material.linewidth = 3;  // 稍粗一点
            }

            // 改变鼠标指针为手型
            this.container.style.cursor = 'pointer';
        } else {
            // 没有悬停在边上
            this.container.style.cursor = 'default';
            this.clearHoverEffect();
        }
    }

    /**
     * 清除悬停高亮效果 - 重写版本，无条件恢复
     */
    clearHoverEffect() {
        if (this.hoveredEdgeId !== null) {
            // 无条件恢复原始颜色（解决时序问题）
            this.edgesGroup.children.forEach(line => {
                if (line.userData.edgeId === this.hoveredEdgeId) {
                    // 恢复默认黑色样式
                    line.material.color.setHex(0x000000);
                    line.material.opacity = 0.6;
                    line.material.linewidth = 2;
                }
            });
            this.hoveredEdgeId = null;
        }
    }

    /**
     * 鼠标点击边
     */
    onEdgeClick(event) {
        // 只有在开启选边模式时才响应点击
        if (!this.edgesGroup || !this.edgeSelectionEnabled) return;

        // 计算鼠标位置（归一化设备坐标）
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        // 射线检测
        this.raycaster.setFromCamera(this.mouse, this.camera);
        this.raycaster.params.Line.threshold = 2;  // 缩小点击容差

        const intersects = this.raycaster.intersectObjects(this.edgesGroup.children, false);

        if (intersects.length > 0) {
            const clickedLine = intersects[0].object;
            const edgeId = clickedLine.userData.edgeId;
            const edgeData = clickedLine.userData.edgeData;

            // 切换选中状态
            if (this.selectedEdges.has(edgeId)) {
                this.deselectEdge(edgeId);
            } else {
                this.selectEdge(edgeId, edgeData);
            }
        }
    }

    /**
     * 设置选边模式开关
     */
    setEdgeSelectionEnabled(enabled) {
        this.edgeSelectionEnabled = enabled;
        console.log(`选边模式: ${enabled ? '开启' : '关闭'}`);

        if (!enabled) {
            // 关闭时清除悬停效果和光标
            this.clearHoverEffect();
            this.container.style.cursor = 'default';
        }
    }

    /**
     * 选中边 - 使用圆柱体实体显示
     */
    selectEdge(edgeId, edgeData) {
        // 第一步：先清除悬停效果（如果当前悬停在这条边上）
        if (this.hoveredEdgeId === edgeId) {
            this.clearHoverEffect();
        }

        this.selectedEdges.add(edgeId);

        // 隐藏原始线段，并强制恢复默认样式（防止黄色残留）
        this.edgesGroup.children.forEach(line => {
            if (line.userData.edgeId === edgeId) {
                line.visible = false;
                // 强制恢复默认样式（即使看不见，也确保状态正确）
                line.material.color.setHex(0x000000);
                line.material.opacity = 0.6;
                line.material.linewidth = 2;
            }
        });

        // 创建圆柱体代替选中的边
        const start = new THREE.Vector3(...edgeData.start);
        const end = new THREE.Vector3(...edgeData.end);
        const direction = new THREE.Vector3().subVectors(end, start);
        const length = direction.length();
        const center = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);

        // 创建圆柱体几何体（固定半径，所有边统一粗细）
        const radius = 0.8;  // 固定半径0.8单位（所有边统一视觉粗细）
        const geometry = new THREE.CylinderGeometry(radius, radius, length, 8);

        // 创建蓝色材质（实体）
        const material = new THREE.MeshStandardMaterial({
            color: 0x2196f3,      // 蓝色
            metalness: 0.5,
            roughness: 0.3,
            emissive: 0x2196f3,   // 自发光蓝色
            emissiveIntensity: 0.3
        });

        const cylinder = new THREE.Mesh(geometry, material);

        // 定位和旋转圆柱体
        cylinder.position.copy(center);
        cylinder.quaternion.setFromUnitVectors(
            new THREE.Vector3(0, 1, 0),  // 圆柱体默认沿Y轴
            direction.normalize()
        );

        cylinder.userData.edgeId = edgeId;
        cylinder.userData.edgeHash = edgeData.hash;  // 保存hash用于回溯
        this.selectedEdgesGroup.add(cylinder);

        console.log(`选中边 ${edgeId}`);
        this.updateEdgeList();
    }

    /**
     * 取消选中边
     */
    deselectEdge(edgeId) {
        this.selectedEdges.delete(edgeId);

        // 显示原始线段，并强制恢复默认样式（第三层保护）
        this.edgesGroup.children.forEach(line => {
            if (line.userData.edgeId === edgeId) {
                line.visible = true;
                // 强制恢复默认黑色样式
                line.material.color.setHex(0x000000);
                line.material.opacity = 0.6;
                line.material.linewidth = 2;
            }
        });

        // 移除圆柱体
        const cylinderToRemove = this.selectedEdgesGroup.children.find(
            cyl => cyl.userData.edgeId === edgeId
        );
        if (cylinderToRemove) {
            this.selectedEdgesGroup.remove(cylinderToRemove);
            cylinderToRemove.geometry.dispose();
            cylinderToRemove.material.dispose();
        }

        console.log(`取消选中边 ${edgeId}`);
        this.updateEdgeList();
    }

    /**
     * 清空所有选中的边
     */
    clearSelectedEdges() {
        this.selectedEdges.forEach(edgeId => {
            this.deselectEdge(edgeId);
        });
        this.selectedEdges.clear();
        this.updateEdgeList();
    }

    /**
     * 获取已选中边的列表
     */
    getSelectedEdges() {
        return Array.from(this.selectedEdges).map(edgeId => {
            return this.edgesData.find(e => e.id === edgeId);
        });
    }

    /**
     * 更新边列表UI（需要在main.js中实现具体UI更新）
     */
    updateEdgeList() {
        const event = new CustomEvent('edgeSelectionChanged', {
            detail: {
                selectedEdges: this.getSelectedEdges(),
                count: this.selectedEdges.size
            }
        });
        window.dispatchEvent(event);
    }
}