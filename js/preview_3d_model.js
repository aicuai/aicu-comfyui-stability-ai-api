import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Three.jsをインポートするヘルパー関数
async function loadThreeJS() {
    if (window.THREE) return;
    
    // Three.jsの主要コンポーネントを動的にロード
    const [THREE, OrbitControls, GLTFLoader, OBJLoader, MTLLoader, PLYLoader] = await Promise.all([
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js'),
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/controls/OrbitControls.js'),
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/loaders/GLTFLoader.js'),
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/loaders/OBJLoader.js'),
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/loaders/MTLLoader.js'),
        import('https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/loaders/PLYLoader.js'),
    ]);

    // グローバルにThree.jsオブジェクトを設定
    window.THREE = THREE;
    window.OrbitControls = OrbitControls.OrbitControls;
    window.GLTFLoader = GLTFLoader.GLTFLoader;
    window.OBJLoader = OBJLoader.OBJLoader;
    window.MTLLoader = MTLLoader.MTLLoader;
    window.PLYLoader = PLYLoader.PLYLoader;
}

app.registerExtension({
    name: "Stability.Preview3DModel",
    async setup() {
        // 3Dプレビューダイアログを作成する関数
        const createPreviewDialog = async (modelData, modelType) => {
            // Three.jsをロード
            await loadThreeJS();

            // ダイアログを作成
            const dialog = document.createElement('dialog');
            dialog.style.cssText = `
                width: 800px;
                height: 600px;
                padding: 20px;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 5px;
                color: white;
            `;

            // タイトルバーを作成
            const titleBar = document.createElement('div');
            titleBar.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            `;

            const title = document.createElement('h3');
            title.textContent = "3D Model Preview";
            title.style.margin = '0';

            const closeButton = document.createElement('button');
            closeButton.textContent = '×';
            closeButton.style.cssText = `
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
            `;
            closeButton.onclick = () => dialog.close();

            titleBar.appendChild(title);
            titleBar.appendChild(closeButton);

            // 3Dビューアーのコンテナを作成
            const container = document.createElement('div');
            container.style.cssText = `
                width: 100%;
                height: 500px;
                background: #2a2a2a;
                border-radius: 5px;
            `;

            dialog.appendChild(titleBar);
            dialog.appendChild(container);
            document.body.appendChild(dialog);

            // Three.jsのシーンをセットアップ
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x2a2a2a);

            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.z = 5;

            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);

            // ライトを追加
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(0, 1, 0);
            scene.add(directionalLight);

            // カメラコントロールを設定
            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // モデルデータをBlobに変換
            const modelBlob = new Blob([modelData], { type: 'application/octet-stream' });
            const modelUrl = URL.createObjectURL(modelBlob);

            // モデルタイプに応じてローダーを選択
            let modelPromise;
            switch (modelType.toLowerCase()) {
                case 'glb':
                case 'gltf':
                    modelPromise = loadGLTF(modelUrl);
                    break;
                case 'obj':
                    modelPromise = loadOBJ(modelUrl);
                    break;
                case 'ply':
                    modelPromise = loadPLY(modelUrl);
                    break;
                default:
                    console.error('Unsupported model type:', modelType);
                    dialog.close();
                    return;
            }

            try {
                const model = await modelPromise;
                scene.add(model);

                // モデルを中央に配置し、カメラの位置を調整
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                model.position.sub(center);

                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                camera.position.z = maxDim * 2;

                // アニメーションループを開始
                function animate() {
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }
                animate();

            } catch (error) {
                console.error('Error loading model:', error);
                dialog.close();
            }

            // Clean up
            URL.revokeObjectURL(modelUrl);

            // ウィンドウリサイズ対応
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });

            // ダイアログを表示
            dialog.showModal();
        };

        // GLTFモデルを読み込む関数
        function loadGLTF(url) {
            return new Promise((resolve, reject) => {
                const loader = new GLTFLoader();
                loader.load(url, (gltf) => {
                    resolve(gltf.scene);
                }, undefined, reject);
            });
        }

        // OBJモデルを読み込む関数
        function loadOBJ(url) {
            return new Promise((resolve, reject) => {
                const loader = new OBJLoader();
                loader.load(url, resolve, undefined, reject);
            });
        }

        // PLYモデルを読み込む関数
        function loadPLY(url) {
            return new Promise((resolve, reject) => {
                const loader = new PLYLoader();
                loader.load(url, (geometry) => {
                    geometry.computeVertexNormals();
                    const material = new THREE.MeshStandardMaterial({
                        color: 0x0055ff,
                        flatShading: true
                    });
                    const mesh = new THREE.Mesh(geometry, material);
                    resolve(mesh);
                }, undefined, reject);
            });
        }

        // プレビューイベントのハンドラーを登録
        api.addEventListener("preview_3d_model", ({ detail }) => {
            const { model_data, model_type } = detail;
            createPreviewDialog(model_data, model_type);
        });
    }
});