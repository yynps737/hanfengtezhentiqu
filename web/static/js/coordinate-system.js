/**
 * 坐标系管理模块
 * 处理CAD（Z向上）和Three.js（Y向上）之间的转换
 */

import * as THREE from 'three';

export class CoordinateSystem {

    /**
     * 坐标系配置
     */
    static SYSTEMS = {
        // 标准Three.js坐标系（Y向上）
        THREEJS: {
            name: 'Three.js标准',
            up: [0, 1, 0],      // Y向上
            right: [1, 0, 0],    // X向右
            forward: [0, 0, 1],  // Z向前（向屏幕外）
            colors: {
                x: 0xff0000,  // 红色
                y: 0x00ff00,  // 绿色
                z: 0x0000ff   // 蓝色
            }
        },

        // CAD标准坐标系（Z向上）
        CAD: {
            name: 'CAD标准',
            up: [0, 0, 1],      // Z向上
            right: [1, 0, 0],    // X向右
            forward: [0, 1, 0],  // Y向前
            colors: {
                x: 0xff0000,  // 红色
                y: 0x00ff00,  // 绿色
                z: 0x0000ff   // 蓝色
            }
        },

        // OpenCASCADE/STEP标准（Z向上）
        OCCT: {
            name: 'OpenCASCADE',
            up: [0, 0, 1],      // Z向上（CAD标准）
            right: [1, 0, 0],    // X向右
            forward: [0, 1, 0],  // Y向前
            colors: {
                x: 0xff0000,  // 红色
                y: 0x00ff00,  // 绿色
                z: 0x0000ff   // 蓝色
            }
        }
    };

    /**
     * 创建标准坐标轴助手
     */
    static createAxesHelper(size = 50, system = 'THREEJS') {
        const config = this.SYSTEMS[system];
        const group = new THREE.Group();
        group.name = 'axesHelper';

        // 创建三个轴
        const axes = [
            { dir: config.right, color: config.colors.x, label: 'X' },
            { dir: config.forward, color: config.colors.y, label: 'Y' },
            { dir: config.up, color: config.colors.z, label: 'Z' }
        ];

        axes.forEach((axis, index) => {
            // 创建轴线
            const geometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(
                    axis.dir[0] * size,
                    axis.dir[1] * size,
                    axis.dir[2] * size
                )
            ]);

            const material = new THREE.LineBasicMaterial({
                color: axis.color,
                linewidth: 2
            });

            const line = new THREE.Line(geometry, material);
            group.add(line);

            // 创建箭头
            const arrowGeometry = new THREE.ConeGeometry(size * 0.05, size * 0.15, 8);
            const arrowMaterial = new THREE.MeshBasicMaterial({ color: axis.color });
            const arrow = new THREE.Mesh(arrowGeometry, arrowMaterial);

            // 设置箭头位置和方向
            arrow.position.set(
                axis.dir[0] * size * 0.95,
                axis.dir[1] * size * 0.95,
                axis.dir[2] * size * 0.95
            );

            // 让箭头指向正确方向
            const direction = new THREE.Vector3(...axis.dir);
            arrow.lookAt(direction.multiplyScalar(size * 1.2));

            group.add(arrow);

            // 添加文字标签
            this.addAxisLabel(group, axis.label, axis.dir, size, axis.color);
        });

        return group;
    }

    /**
     * 添加轴标签
     */
    static addAxisLabel(group, label, direction, size, color) {
        // 创建精灵标签
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 64;
        canvas.height = 64;

        context.font = 'Bold 48px Arial';
        context.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(label, 32, 32);

        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({
            map: texture,
            alphaTest: 0.1,
            transparent: true
        });

        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.position.set(
            direction[0] * size * 1.2,
            direction[1] * size * 1.2,
            direction[2] * size * 1.2
        );
        sprite.scale.set(size * 0.2, size * 0.2, 1);

        group.add(sprite);
    }

    /**
     * 转换模型从CAD坐标系到Three.js坐标系
     * CAD: Z向上 -> Three.js: Y向上
     */
    static convertCADToThreeJS(object) {
        // 旋转-90度绕X轴，将Z向上转换为Y向上
        const rotationMatrix = new THREE.Matrix4();
        rotationMatrix.makeRotationX(-Math.PI / 2);
        object.applyMatrix4(rotationMatrix);
        return object;
    }

    /**
     * 转换模型从Three.js坐标系到CAD坐标系
     * Three.js: Y向上 -> CAD: Z向上
     */
    static convertThreeJSToCAD(object) {
        // 旋转90度绕X轴，将Y向上转换为Z向上
        const rotationMatrix = new THREE.Matrix4();
        rotationMatrix.makeRotationX(Math.PI / 2);
        object.applyMatrix4(rotationMatrix);
        return object;
    }

    /**
     * 创建坐标系指示器（显示在角落）
     */
    static createViewHelper(size = 100) {
        const helper = new THREE.Group();

        // 创建一个小的坐标轴显示
        const axes = this.createAxesHelper(size / 2);
        helper.add(axes);

        // 创建背景球
        const sphereGeometry = new THREE.SphereGeometry(size * 0.4, 16, 16);
        const sphereMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            opacity: 0.2,
            transparent: true
        });
        const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        helper.add(sphere);

        return helper;
    }

    /**
     * 获取当前坐标系的网格方向
     */
    static getGridOrientation(system = 'THREEJS') {
        const config = this.SYSTEMS[system];

        if (system === 'CAD' || system === 'OCCT') {
            // CAD模式：XY平面（Z向上）
            return {
                rotation: [0, 0, 0],
                position: 'bottom'  // 放在模型底部
            };
        } else {
            // Three.js模式：XZ平面（Y向上）
            return {
                rotation: [Math.PI / 2, 0, 0],
                position: 'bottom'  // 放在模型底部
            };
        }
    }
}