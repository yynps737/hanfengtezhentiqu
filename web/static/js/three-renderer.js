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

        this.init();
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
}