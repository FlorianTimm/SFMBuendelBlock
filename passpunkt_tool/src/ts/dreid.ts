import Tool from "./tool";
import * as THREE from 'three';
//import { Scene, PerspectiveCamera, WebGLRenderer, BoxGeometry, MeshBasicMaterial, Mesh } from 'three';
import GUI from ".";
import { Bild, Passpunkt } from "./types";
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';



export default class DreiD extends Tool {
    private scene: THREE.Scene;
    private camera: THREE.Camera;
    private renderer: THREE.WebGLRenderer;
    private controls: OrbitControls;
    //private running = false;

    async start() {
        await this.loadPoints();
        this.animate()
    }

    stop() {
    }

    constructor(gui: GUI) {
        super(gui)
        this.scene = new THREE.Scene();
        //this.camera = new THREE.OrthographicCamera(undefined, undefined, undefined, undefined, 0.1, 1000);
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

        this.renderer = new THREE.WebGLRenderer();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById("dreid")?.appendChild(this.renderer.domElement);


        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.minDistance = 0;
        this.controls.maxDistance = Infinity;

        this.controls.enableZoom = true; // Set to false to disable zooming
        this.controls.zoomSpeed = 1.5;

        this.controls.enablePan = true;

        this.camera.position.z = 5;
        this.controls.addEventListener('change', this.render.bind(this)); // call this only in static scenes (i.e., if there is no animation loop)

    }
    /*
        private animate() {
            if (this.running) requestAnimationFrame(this.animate.bind(this));
            this.cube.rotation.x += 0.01;
            this.cube.rotation.y += 0.01;
            console.log("Bla")
            this.renderer.render(this.scene, this.camera);
        }
        */

    private async loadPoints() {
        this.scene.clear()
        let punkte: Passpunkt[] = await fetch("/api/" + this.gui.projekt + "/passpunkte/").then((res) => res.json())
        for (let punkt of punkte) {
            if (punkt.x && punkt.y && punkt.z)
                this.drawPoint(punkt)
        }

        let bilder: Bild[] = await fetch("/api/" + this.gui.projekt + "/images/").then((res) => res.json())
        for (let bild of bilder) {
            if (bild.x && bild.y && bild.z)
                this.drawPicture(bild)
        }

    }

    private drawPoint(punkt: Passpunkt) {
        if (!(punkt.x && punkt.y && punkt.z)) return
        const geometry = new THREE.BoxGeometry(0.05, 0.05, 0.05);
        let color = 0x555555
        if (punkt.type == "manual")
            color = 0x00ff00
        else if (punkt.type == "aruco")
            color = 0x0000ff
        const material = new THREE.MeshBasicMaterial({ color: color });
        let cube = new THREE.Mesh(geometry, material);
        cube.position.set(punkt.x, punkt.y, punkt.z)
        this.scene.add(cube);
    }

    private drawPicture(bild: Bild) {
        if (!(bild.x && bild.y && bild.z)) return
        const geometry = new THREE.BoxGeometry(0.2, 0.2, 0.2);
        const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
        let cube = new THREE.Mesh(geometry, material);
        cube.position.set(bild.x, bild.y, bild.z)
        this.scene.add(cube);
    }

    private animate() {
        requestAnimationFrame(this.animate.bind(this));
        this.controls.update(); // only required if controls.enableDamping = true, or if controls.autoRotate = true
        this.render();
    }

    private render() {
        this.renderer.render(this.scene, this.camera);
    }
}