import ImageLayer from 'ol/layer/Image';
import Map from 'ol/Map';
import Projection from 'ol/proj/Projection';
import Static from 'ol/source/ImageStatic';
import View from 'ol/View';
import { Extent, getCenter } from 'ol/extent';
import { MapBrowserEvent } from 'ol';
import { saveAs } from "file-saver";
import Tool from './tool';
import GUI from '.';

type Passpunkt = {
    passpunkt: number,
    image: number,
    x: number,
    y: number
}

export default class PasspunktTool extends Tool {

    private passpunkte: Passpunkt[] = []
    private selectPasspunkt: HTMLSelectElement;
    private files: File[] = []

    constructor(gui: GUI) {
        super(gui)
        const layer = new ImageLayer({})

        const map = new Map({
            layers: [
                layer
            ],
            target: 'map',

        });

        let passpunktNr = 0
        this.selectPasspunkt = <HTMLSelectElement>document.getElementById("passpunkt")
        map.on("click", (e: MapBrowserEvent<any>) => {
            console.log(activeImage, e.coordinate, this.selectPasspunkt.value)
            if (parseInt(this.selectPasspunkt.value) == -1) {
                let neu = document.createElement("option")
                neu.value = (passpunktNr++).toString()
                neu.innerHTML = "Passpunkt " + neu.value
                this.selectPasspunkt.appendChild(neu)
                this.selectPasspunkt.selectedIndex = passpunktNr
            }
            this.passpunkte.push({
                passpunkt: parseInt(this.selectPasspunkt.value),
                image: activeImage,
                x: e.coordinate[0],
                y: e.coordinate[1]
            })
            this.refreshListe()
        })
        this.selectPasspunkt.addEventListener("change", this.refreshListe.bind(this))

        let activeImage = -1

        document.getElementById("speichern")?.addEventListener("click", () => {
            let exp: { bilder: string[], passpunkte: Passpunkt[] } = {
                bilder: [],
                passpunkte: this.passpunkte
            }
            for (let file of this.files) {
                exp.bilder.push(file.name)
            }
            let blob = new Blob([JSON.stringify(exp)], { type: "application/json" });
            saveAs(blob, "daten.json")
        })
    }

    stop() {

    }

    start() {

    }


    private imageSize(url: string): Promise<{ width: number, height: number }> {
        const img = document.createElement("img");

        const promise = new Promise<{ width: number, height: number }>((resolve, reject) => {
            img.onload = () => {
                // Natural size is the actual image size regardless of rendering.
                // The 'normal' `width`/`height` are for the **rendered** size.
                const width = img.naturalWidth;
                const height = img.naturalHeight;

                // Resolve promise with the width and height
                resolve({ width: width, height: height });
            };

            // Reject promise on error
            img.onerror = reject;
        });

        // Setting the source makes it start downloading and eventually call `onload`
        img.src = url;

        return promise;
    }

    private async createSource(url: string): Promise<{ view: View; layer: Static; }> {
        let size = await this.imageSize(url)
        console.log(size)
        const extent: Extent = [0, 0, size.width, size.height];
        const projection = new Projection({
            code: 'xkcd-image',
            units: 'pixels',
            extent: extent,
        });
        return {
            layer: new Static({
                url: url,
                projection: projection,
                imageExtent: extent,
            }),
            view: new View({
                projection: projection,
                center: getCenter(extent),
                zoom: 2,
                maxZoom: 8,
            })
        }
    }

    private refreshListe() {
        let liste = document.getElementById("passpunktListe");
        if (!liste) return
        liste.innerHTML = "";
        for (let eintrag of this.passpunkte) {
            if (eintrag.passpunkt != parseInt(this.selectPasspunkt.value)) continue
            let c = document.createElement("canvas");
            let ctx = c.getContext("2d");
            if (!ctx) continue
            let image = new Image();
            image.src = URL.createObjectURL(this.files[eintrag.image]);
            image.onload = function () {
                if (!ctx) return
                ctx.drawImage(image, eintrag.x - 50, image.height - eintrag.y - 50, 100, 100, 0, 0, 100, 100);
            }
            liste?.appendChild(c)
        }
    }

}