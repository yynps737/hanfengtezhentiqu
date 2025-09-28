/**
 * Three.js r180 渲染器模块
 * 使用最新的ES模块方式
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class ThreeRenderer {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentModel = null;
        this.isWireframe = false;
        this.isGridVisible = true;
        this.isAxesVisible = true;
        this.axisMode = 0; // 0: XYZ, 1: XZY, 2: YXZ, 3: YZX, 4: ZXY, 5: ZYX
        this.cadMode = true; // true: CAD模式(Z向上), false: Three.js模式(Y向上)

        // 边选择相关
        this.edgeObjects = [];  // 存储所有边的Three.js对象
        this.selectedEdges = new Set();  // 存储选中的边ID
        this.isEdgeSelectionMode = false;  // 是否在边选择模式
        this.edgeGroup = null;  // 边的组对象
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // 绑定事件处理函数，保持引用以便移除
        this.boundOnEdgeClick = this.onEdgeClick.bind(this);

        this.init();
    }

    init() {
        // 隐藏占位符
        const placeholder = this.container.querySelector('.viewer-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        // 创建场景
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf5f5f5);

        // 创建相机 - Z轴朝上配置
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
        this.camera.position.set(100, 100, 100);
        this.camera.up.set(0, 0, 1); // 设置Z轴为上方向

        // 创建渲染器
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        // 添加到容器
        this.container.appendChild(this.renderer.domElement);

        // 创建控制器（参考Three.js官方示例）
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = true;  // 启用屏幕空间平移
        this.controls.enablePan = true;  // 启用平移
        this.controls.minDistance = 10;
        this.controls.maxDistance = 1000;
        this.controls.maxPolarAngle = Math.PI;  // 允许完全旋转

        // 添加光源
        this.setupLights();

        // 添加辅助对象
        this.setupHelpers();

        // 开始渲染循环
        this.animate();

        // 响应窗口大小变化
        this.setupResize();

        console.log('Three.js r180 渲染器初始化完成');
    }

    setupLights() {
        // 环境光
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        // 方向光
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);

        // 补充光源
        const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.3);
        this.scene.add(hemisphereLight);
    }

    setupHelpers() {
        // 网格辅助线 - 在XY平面（Z=0）
        const gridHelper = new THREE.GridHelper(200, 20, 0x888888, 0xcccccc);
        gridHelper.rotateX(Math.PI / 2); // 旋转到XY平面
        gridHelper.name = 'gridHelper';
        this.scene.add(gridHelper);

        // 坐标轴（初始大小）
        const axesHelper = new THREE.AxesHelper(50);
        axesHelper.name = 'axesHelper';
        this.scene.add(axesHelper);
    }

    updateHelpers(modelSize, modelCenter = new THREE.Vector3(0, 0, 0)) {
        // 移除旧的辅助对象
        const oldGrid = this.scene.getObjectByName('gridHelper');
        const oldAxes = this.scene.getObjectByName('axesHelper');

        if (oldGrid) this.scene.remove(oldGrid);
        if (oldAxes) this.scene.remove(oldAxes);

        // 根据模型大小创建新的辅助对象
        const maxDim = Math.max(modelSize.x, modelSize.y, modelSize.z);
        const gridSize = Math.max(maxDim * 2, 100);
        const axesSize = Math.max(maxDim * 0.5, 25);

        if (this.isGridVisible) {
            this.createOrientedGrid(gridSize, modelCenter);
        }

        if (this.isAxesVisible) {
            // 创建自定义坐标轴
            this.createCustomAxes(axesSize, modelCenter);
        }

        console.log('辅助对象已更新:', {
            gridSize,
            axesSize,
            modelMaxDim: maxDim,
            gridVisible: this.isGridVisible,
            axesVisible: this.isAxesVisible
        });
    }

    setupResize() {
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const { width, height } = entry.contentRect;
                if (width > 0 && height > 0) {
                    this.camera.aspect = width / height;
                    this.camera.updateProjectionMatrix();
                    this.renderer.setSize(width, height);
                }
            }
        });
        resizeObserver.observe(this.container);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.controls) {
            this.controls.update();
        }

        this.renderer.render(this.scene, this.camera);
    }

    displayMesh(meshData) {
        console.log('显示网格数据:', {
            vertices: meshData.vertices ? meshData.vertices.length / 3 : 0,
            faces: meshData.faces ? meshData.faces.length / 3 : 0,
            edges: meshData.edges ? meshData.edges.length : 0
        });

        // 移除之前的模型和边
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
            this.currentModel.geometry?.dispose();
            this.currentModel.material?.dispose();
        }

        if (!meshData || !meshData.vertices || !meshData.faces) {
            console.error('无效的网格数据');
            return;
        }

        // 创建几何体
        const geometry = new THREE.BufferGeometry();

        // 直接使用原始顶点数据，无需转换（因为相机已设置为Z轴朝上）
        const vertices = new Float32Array(meshData.vertices);
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

        // 设置面索引
        const indices = new Uint32Array(meshData.faces);
        geometry.setIndex(new THREE.BufferAttribute(indices, 1));

        // 计算法向量
        geometry.computeVertexNormals();

        // 计算包围盒和包围球
        geometry.computeBoundingBox();
        geometry.computeBoundingSphere();

        // 如果有边数据，创建边对象（用于选择）
        if (meshData.edges && meshData.edges.length > 0) {
            this.createEdgeObjects(meshData.edges);
        }

        // 创建材质
        const material = new THREE.MeshPhongMaterial({
            color: 0x8888cc,
            specular: 0x222222,
            shininess: 100,
            side: THREE.DoubleSide,
            wireframe: this.isWireframe
        });

        // 创建网格对象
        this.currentModel = new THREE.Mesh(geometry, material);
        this.currentModel.name = 'model';
        this.currentModel.castShadow = true;
        this.currentModel.receiveShadow = true;

        // 添加到场景
        this.scene.add(this.currentModel);

        // 调整相机视角
        this.fitCameraToObject(this.currentModel);

        // 更新辅助对象大小
        const finalBox = new THREE.Box3().setFromObject(this.currentModel);
        const finalSize = finalBox.getSize(new THREE.Vector3());
        const finalCenter = finalBox.getCenter(new THREE.Vector3());
        this.updateHelpers(finalSize, finalCenter);

        console.log('模型添加到场景，场景子对象数量:', this.scene.children.length);
    }

    fitCameraToObject(object) {
        const box = new THREE.Box3().setFromObject(object);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());

        console.log('模型原始尺寸:', {
            size: { x: size.x, y: size.y, z: size.z },
            center: { x: center.x, y: center.y, z: center.z }
        });

        // 计算模型的最大尺寸
        const maxDim = Math.max(size.x, size.y, size.z);

        // 如果模型太大或太小，进行缩放
        let scale = 1;
        const targetSize = 100; // 目标尺寸

        if (maxDim > targetSize * 5) {
            // 模型太大，缩小
            scale = targetSize / maxDim;
        } else if (maxDim < targetSize * 0.1) {
            // 模型太小，放大
            scale = targetSize / maxDim;
        }

        // 应用缩放
        if (scale !== 1) {
            object.scale.setScalar(scale);
            console.log('模型缩放比例:', scale);

            // 重新计算包围盒
            box.setFromObject(object);
            box.getSize(size);
            box.getCenter(center);
        }

        // 将模型移动到原点附近
        object.position.set(-center.x, -center.y, -center.z);

        // 重新计算最终位置的包围盒
        box.setFromObject(object);
        const finalSize = box.getSize(new THREE.Vector3());
        const finalCenter = box.getCenter(new THREE.Vector3());
        const finalMaxDim = Math.max(finalSize.x, finalSize.y, finalSize.z);

        // 计算合适的相机距离
        const fov = this.camera.fov * (Math.PI / 180);
        const distance = finalMaxDim / (2 * Math.tan(fov / 2)) * 1.5;

        // 设置相机位置
        this.camera.position.set(
            finalCenter.x + distance * 0.7,
            finalCenter.y + distance * 0.7,
            finalCenter.z + distance * 0.7
        );

        this.camera.lookAt(finalCenter);

        // 更新控制器
        this.controls.target.copy(finalCenter);
        this.controls.maxDistance = distance * 5;
        this.controls.minDistance = finalMaxDim * 0.1;
        this.controls.update();

        console.log('模型已调整:', {
            finalSize: { x: finalSize.x, y: finalSize.y, z: finalSize.z },
            finalCenter: { x: finalCenter.x, y: finalCenter.y, z: finalCenter.z },
            cameraDistance: distance,
            scale: scale
        });
    }

    highlightWelds(welds) {
        if (!welds || welds.length === 0) return;

        // 移除之前的焊缝高亮
        const oldHighlights = this.scene.children.filter(child =>
            child.userData.isWeldHighlight
        );
        oldHighlights.forEach(obj => {
            this.scene.remove(obj);
            obj.geometry?.dispose();
            obj.material?.dispose();
        });

        // 计算合适的标记大小
        let markerSize = 2; // 默认大小
        if (this.currentModel) {
            const box = new THREE.Box3().setFromObject(this.currentModel);
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            markerSize = maxDim * 0.02; // 模型尺寸的2%
            markerSize = Math.max(0.5, Math.min(markerSize, 10)); // 限制在0.5-10之间
        }

        // 添加新的焊缝高亮
        welds.forEach((weld) => {
            const geometry = new THREE.SphereGeometry(markerSize, 16, 16);

            // 根据焊缝类型设置颜色
            let color = 0x9f7aea; // 默认紫色
            switch (weld.type) {
                case 'fillet':
                    color = 0x48bb78; // 绿色
                    break;
                case 'butt':
                    color = 0xed8936; // 橙色
                    break;
                case 'lap':
                    color = 0x3182ce; // 蓝色
                    break;
            }

            const material = new THREE.MeshBasicMaterial({
                color: color,
                opacity: 0.8,
                transparent: true
            });

            const sphere = new THREE.Mesh(geometry, material);

            // 应用模型的缩放和位移变换（无需坐标系转换）
            if (this.currentModel) {
                const modelScale = this.currentModel.scale.x;
                const modelPosition = this.currentModel.position;

                sphere.position.set(
                    (weld.position[0] * modelScale) + modelPosition.x,
                    (weld.position[1] * modelScale) + modelPosition.y,
                    (weld.position[2] * modelScale) + modelPosition.z
                );
            } else {
                sphere.position.set(...weld.position);
            }

            sphere.userData.isWeldHighlight = true;
            sphere.userData.weldData = weld;

            this.scene.add(sphere);
        });

        console.log(`添加了 ${welds.length} 个焊缝高亮标记，标记大小: ${markerSize.toFixed(2)}`);
    }

    resetView() {
        if (this.currentModel) {
            this.fitCameraToObject(this.currentModel);
        } else {
            this.camera.position.set(100, 100, 100);
            this.camera.up.set(0, 0, 1); // 确保Z轴朝上
            this.camera.lookAt(0, 0, 0);
            this.controls.target.set(0, 0, 0);
            this.controls.update();
        }
    }

    toggleWireframe() {
        this.isWireframe = !this.isWireframe;

        if (this.currentModel && this.currentModel.material) {
            this.currentModel.material.wireframe = this.isWireframe;
        }

        console.log('线框模式:', this.isWireframe ? '开启' : '关闭');
    }

    toggleGrid() {
        this.isGridVisible = !this.isGridVisible;

        const gridHelper = this.scene.getObjectByName('gridHelper');
        if (gridHelper) {
            gridHelper.visible = this.isGridVisible;
        }

        console.log('网格显示:', this.isGridVisible ? '开启' : '关闭');
    }

    toggleAxes() {
        this.isAxesVisible = !this.isAxesVisible;

        const axesHelper = this.scene.getObjectByName('axesHelper');
        if (axesHelper) {
            axesHelper.visible = this.isAxesVisible;
        }

        console.log('坐标轴显示:', this.isAxesVisible ? '开启' : '关闭');
    }

    createCustomAxes(size, position) {
        // 移除旧的坐标轴
        const oldAxes = this.scene.getObjectByName('axesHelper');
        if (oldAxes) {
            this.scene.remove(oldAxes);
        }

        // 坐标轴变换配置
        const axisConfigs = [
            { name: 'XYZ', x: [1,0,0], y: [0,1,0], z: [0,0,1] }, // 标准
            { name: 'XZY', x: [1,0,0], y: [0,0,1], z: [0,1,0] }, // Y和Z交换
            { name: 'YXZ', x: [0,1,0], y: [1,0,0], z: [0,0,1] }, // X和Y交换
            { name: 'YZX', x: [0,0,1], y: [0,1,0], z: [1,0,0] }, // 循环：X→Z, Y→X, Z→Y
            { name: 'ZXY', x: [0,1,0], y: [0,0,1], z: [1,0,0] }, // 循环：X→Y, Y→Z, Z→X
            { name: 'ZYX', x: [0,0,1], y: [1,0,0], z: [0,1,0] }  // X和Z交换
        ];

        const config = axisConfigs[this.axisMode];

        // 创建坐标轴组
        const axesGroup = new THREE.Group();
        axesGroup.name = 'axesHelper';
        axesGroup.position.copy(position);

        // 材质
        const xMaterial = new THREE.LineBasicMaterial({ color: 0xff0000 }); // 红色
        const yMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00 }); // 绿色
        const zMaterial = new THREE.LineBasicMaterial({ color: 0x0000ff }); // 蓝色

        // 创建X轴
        const xGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(config.x[0] * size, config.x[1] * size, config.x[2] * size)
        ]);
        const xLine = new THREE.Line(xGeometry, xMaterial);
        axesGroup.add(xLine);

        // 创建Y轴
        const yGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(config.y[0] * size, config.y[1] * size, config.y[2] * size)
        ]);
        const yLine = new THREE.Line(yGeometry, yMaterial);
        axesGroup.add(yLine);

        // 创建Z轴
        const zGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(config.z[0] * size, config.z[1] * size, config.z[2] * size)
        ]);
        const zLine = new THREE.Line(zGeometry, zMaterial);
        axesGroup.add(zLine);

        // 添加轴标签
        this.addAxisLabels(axesGroup, config, size);

        this.scene.add(axesGroup);

        console.log(`坐标轴已切换到: ${config.name}`);
    }

    addAxisLabels(axesGroup, config, size) {
        const labels = ['X', 'Y', 'Z'];
        const colors = ['#ff0000', '#00ff00', '#0000ff'];
        const directions = [config.x, config.y, config.z];

        labels.forEach((label, i) => {
            // 为每个标签创建独立的canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = 64;
            canvas.height = 64;

            // 清空画布并绘制当前标签
            context.clearRect(0, 0, 64, 64);
            context.font = 'Bold 48px Arial';
            context.fillStyle = colors[i];
            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.fillText(label, 32, 32);

            // 创建纹理和精灵
            const texture = new THREE.CanvasTexture(canvas);
            texture.needsUpdate = true; // 确保纹理更新
            const spriteMaterial = new THREE.SpriteMaterial({
                map: texture,
                alphaTest: 0.1
            });
            const sprite = new THREE.Sprite(spriteMaterial);

            // 设置位置（轴端点稍外一点）
            const dir = directions[i];
            sprite.position.set(
                dir[0] * size * 1.1,
                dir[1] * size * 1.1,
                dir[2] * size * 1.1
            );
            sprite.scale.set(size * 0.15, size * 0.15, 1);

            axesGroup.add(sprite);
        });
    }

    createOrientedGrid(size, center) {
        // 移除旧网格
        const oldGrid = this.scene.getObjectByName('gridHelper');
        if (oldGrid) {
            this.scene.remove(oldGrid);
            oldGrid.geometry?.dispose();
            oldGrid.material?.dispose();
        }

        // 创建网格（默认在XZ平面）
        const gridHelper = new THREE.GridHelper(
            size,
            Math.max(20, Math.floor(size / 10)),
            0x888888,
            0xcccccc
        );
        gridHelper.name = 'gridHelper';

        // 旋转到XY平面（因为我们使用Z轴朝上）
        gridHelper.rotateX(Math.PI / 2);

        // 设置位置在模型底部
        gridHelper.position.copy(center);
        if (this.currentModel) {
            const box = new THREE.Box3().setFromObject(this.currentModel);
            gridHelper.position.z = box.min.z - 1; // 在模型底部
        }

        this.scene.add(gridHelper);
    }

    switchAxisMode() {
        // Z轴朝上模式下，简化为只切换视角
        console.log('切换视角模式');

        // 重置相机视角
        if (this.currentModel) {
            this.resetView();
        }
    }

    clearHighlights() {
        // 清除所有焊缝/接头高亮标记
        const highlightsToRemove = this.scene.children.filter(child =>
            child.userData.isWeldHighlight
        );

        highlightsToRemove.forEach(obj => {
            this.scene.remove(obj);
            obj.geometry?.dispose();
            obj.material?.dispose();
        });

        console.log(`清除了 ${highlightsToRemove.length} 个高亮标记`);
    }

    clearAll() {
        // 清除模型
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
            this.currentModel.geometry?.dispose();
            this.currentModel.material?.dispose();
            this.currentModel = null;
        }

        // 清除高亮
        this.clearHighlights();
    }

    // 边选择功能
    enterEdgeSelectionMode() {
        this.isEdgeSelectionMode = true;
        this.selectedEdges.clear();

        // 添加点击事件监听
        this.renderer.domElement.addEventListener('click', this.boundOnEdgeClick);

        // 显示所有边
        this.showAllEdges();

        console.log('进入边选择模式');
        console.log('当前边对象数量:', this.edgeObjects.length);
    }

    exitEdgeSelectionMode() {
        this.isEdgeSelectionMode = false;

        // 移除点击事件监听
        this.renderer.domElement.removeEventListener('click', this.boundOnEdgeClick);

        // 隐藏边
        this.hideAllEdges();

        console.log('退出边选择模式');
    }

    showAllEdges() {
        if (!this.edgeGroup) return;

        this.edgeGroup.visible = true;

        // 重置所有边的颜色
        this.edgeGroup.children.forEach(edge => {
            edge.material.color.setHex(0x0000ff);  // 默认蓝色
        });
    }

    hideAllEdges() {
        if (this.edgeGroup) {
            this.edgeGroup.visible = false;
        }
    }

    createEdgeObjects(edgesData) {
        // 移除旧的边组
        if (this.edgeGroup) {
            this.scene.remove(this.edgeGroup);
            this.edgeGroup.children.forEach(child => {
                child.geometry?.dispose();
                child.material?.dispose();
            });
        }

        // 清空边对象数组
        this.edgeObjects = [];

        // 创建新的边组
        this.edgeGroup = new THREE.Group();
        this.edgeGroup.name = 'edges';
        this.edgeGroup.visible = false;  // 默认隐藏

        edgesData.forEach(edgeData => {
            const points = [];
            for (let i = 0; i < edgeData.points.length; i += 3) {
                points.push(new THREE.Vector3(
                    edgeData.points[i],
                    edgeData.points[i + 1],
                    edgeData.points[i + 2]
                ));
            }

            // 创建线条几何体
            const geometry = new THREE.BufferGeometry().setFromPoints(points);

            // 创建材质
            const material = new THREE.LineBasicMaterial({
                color: 0x0000ff,  // 默认蓝色
                linewidth: 3
            });

            // 创建线条对象
            const line = new THREE.Line(geometry, material);
            line.userData.edgeId = edgeData.id;
            line.name = edgeData.id;

            this.edgeGroup.add(line);
            this.edgeObjects.push(line);
        });

        this.scene.add(this.edgeGroup);
        console.log(`创建了 ${edgesData.length} 条边的显示对象`);
    }

    onEdgeClick(event) {
        if (!this.isEdgeSelectionMode) return;

        console.log('点击事件触发, 边对象数量:', this.edgeObjects.length);

        // 计算鼠标位置
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        // 发射射线
        this.raycaster.setFromCamera(this.mouse, this.camera);

        // 检测交叉的边
        const intersects = this.raycaster.intersectObjects(this.edgeObjects);
        console.log('检测到的交叉对象:', intersects.length);

        if (intersects.length > 0) {
            const clickedEdge = intersects[0].object;
            const edgeId = clickedEdge.userData.edgeId;

            this.toggleEdgeSelection(edgeId, clickedEdge);
        }
    }

    toggleEdgeSelection(edgeId, edgeObject) {
        if (this.selectedEdges.has(edgeId)) {
            // 取消选择
            this.selectedEdges.delete(edgeId);
            edgeObject.material.color.setHex(0x0000ff);  // 恢复蓝色
            console.log(`取消选中边: ${edgeId}, 当前选中数量: ${this.selectedEdges.size}`);
        } else {
            // 选择边
            this.selectedEdges.add(edgeId);
            edgeObject.material.color.setHex(0x9f00ff);  // 紫色高亮
            console.log(`选中边: ${edgeId}, 当前选中数量: ${this.selectedEdges.size}`);

        // 通知EdgeSelector更新选中列表
        const event = new CustomEvent('edgeSelectionChanged', {
            detail: { selectedEdges: Array.from(this.selectedEdges) }
        });
        document.dispatchEvent(event);
    }

    getSelectedEdges() {
        console.log('获取选中的边, 数量:', this.selectedEdges.size, '边ID:', Array.from(this.selectedEdges));
        return Array.from(this.selectedEdges);
    }

    dispose() {
        // 清理资源
        if (this.currentModel) {
            this.currentModel.geometry?.dispose();
            this.currentModel.material?.dispose();
        }

        // 清理边对象
        if (this.edgeGroup) {
            this.edgeGroup.children.forEach(child => {
                child.geometry?.dispose();
                child.material?.dispose();
            });
            this.scene.remove(this.edgeGroup);
        }

        this.renderer?.dispose();
        this.controls?.dispose();

        if (this.container.contains(this.renderer?.domElement)) {
            this.container.removeChild(this.renderer.domElement);
        }
    }
}