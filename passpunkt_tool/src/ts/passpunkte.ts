import ImageLayer from 'ol/layer/Image';
import Map from 'ol/Map';
import Projection from 'ol/proj/Projection';
import Static from 'ol/source/ImageStatic';
import View from 'ol/View';
import { Extent, getCenter } from 'ol/extent';
import { Feature, MapBrowserEvent } from 'ol';
import Tool from './tool';
import GUI from '.';
import ImageSource from 'ol/source/Image';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Bild, Passpunkt, PasspunktPosition } from './types';
import { Point } from 'ol/geom';
import {
    Circle as CircleStyle,
    Fill,
    Stroke,
    Style,
    Text,
} from 'ol/style';
import {
    Select as SelectInteraction,
    Modify as ModifyInteraction,
    defaults as defaultInteraction
} from 'ol/interaction';
import { SelectEvent } from 'ol/interaction/Select';
import { ModifyEvent } from 'ol/interaction/Modify';



export default class PasspunktTool extends Tool {
    private passpunkte: PasspunktPosition[] = []
    private selectPasspunkt: HTMLSelectElement;
    private bildliste: HTMLDivElement;
    private bilder: Bild[] = [];
    private map: Map;
    private activeImage: Bild | undefined
    private layer: ImageLayer<ImageSource>;
    private punktLayerSource: VectorSource;
    private passpunktNr: number = 0

    constructor(gui: GUI) {
        super(gui)
        this.layer = new ImageLayer({})
        this.punktLayerSource = new VectorSource({})
        let punktLayer = new VectorLayer<VectorSource>({
            source: this.punktLayerSource,
            style: (feat) => {
                return new Style({
                    text: new Text({
                        text: feat.get('name').toString(),
                        font: '13px Calibri,sans-serif',
                        fill: new Fill({ color: '#000' }),
                        stroke: new Stroke({
                            color: '#fff', width: 2
                        }),
                        offsetX: 9,
                        offsetY: 8,
                        textAlign: 'left'
                    }),
                    image: new CircleStyle({
                        radius: 5,
                        fill: new Fill({ color: 'rgba(255, 0, 0, 0.1)' }),
                        stroke: new Stroke({ color: 'red', width: 1 }),
                    }),
                })
            }
        })
        let selectInteraction = new SelectInteraction({
            layers: [punktLayer]
        })
        selectInteraction.on("select", this.passpunktAufBildAusgewaehlt.bind(this))

        let modifyInteraction = new ModifyInteraction({
            features: selectInteraction.getFeatures(),
        })
        modifyInteraction.on("modifyend", this.passpunktAufBildVerschoben.bind(this))

        this.map = new Map({
            layers: [
                this.layer,
                punktLayer
            ],
            interactions: defaultInteraction().extend([selectInteraction, modifyInteraction]),
            target: 'map',

        });

        this.bildliste = <HTMLDivElement>document.getElementById("passpunktBildListe")

        this.selectPasspunkt = <HTMLSelectElement>document.getElementById("passpunktSelect")
        this.selectPasspunkt.addEventListener("change", this.refreshListe.bind(this))
    }

    private passpunktAufBildAusgewaehlt(e: SelectEvent) {
        console.log(e)
        if (e.selected.length > 0) {
            this.selectPasspunkt.value = e.selected[0].get("passpunkt")
            this.selectPasspunkt.dispatchEvent(new Event("change"))
        }
    }

    private passpunktAufBildVerschoben(e: ModifyEvent) {
        console.log(e)
    }

    private passpunktClick(e: MapBrowserEvent<any>) {
        if (!this.activeImage) return;

        console.log(this.punktLayerSource.getFeaturesAtCoordinate(e.coordinate))

        console.log(this.activeImage, e.coordinate, this.selectPasspunkt.value)
        if (parseInt(this.selectPasspunkt.value) == -1) {
            let neu = document.createElement("option")
            neu.value = (this.passpunktNr++).toString()
            neu.innerHTML = "Passpunkt " + neu.value
            this.selectPasspunkt.appendChild(neu)
            this.selectPasspunkt.selectedIndex = this.passpunktNr
        }

        this.passpunkte.push({
            passpunkt: parseInt(this.selectPasspunkt.value),
            name: this.selectPasspunkt.innerText,
            image: this.activeImage.bid,
            x: e.coordinate[0],
            y: e.coordinate[1]
        })
        this.refreshListe()
    }

    stop() {

    }

    async start() {
        this.bilder = await fetch("/api/" + this.gui.projekt + "/images/").then((res) => res.json())
        this.bildliste.innerHTML = "";
        let firstImage = true
        for (let bild of this.bilder) {
            let img = document.createElement("img")
            img.src = bild.url;
            this.bildliste.appendChild(img)
            img.addEventListener("click", () => this.bildauswahl(bild))
            if (firstImage) {
                firstImage = false;
                this.bildauswahl(bild)
            }
        }

        this.loadPasspunkte()


        /*
for (let file of this.fileSelect.files) {
    if (!file) return;
    this.files.push(file)

    let img = document.createElement('img')
    img.src = URL.createObjectURL(file)
    img.style.width = "90%"
    img.style.display = "block"
    let imgNr = this.files.length - 1
    document.getElementById("nav")?.appendChild(img)
    img.addEventListener("click", async () => {
        let daten = await this.createSource(img.src)
        layer.setSource(daten.layer);
        map.setView(daten.view)
        activeImage = imgNr
    })
}*/
    }

    private async bildauswahl(bild: Bild) {
        let daten = await this.createSource(bild.url)
        this.layer.setSource(daten.layer);
        this.map.setView(daten.view)
        this.activeImage = bild
        this.loadPasspunktPosAufBild(bild.bid)
    }

    private async loadPasspunktPosAufBild(bildId: number) {
        let passpunkte: PasspunktPosition[] = await fetch("/api/" + this.gui.projekt + "/image/" + bildId + "/passpunkte").then((res) => res.json())
        this.punktLayerSource.clear()
        let width = 4000;
        let height = 3000;
        for (let passpunkt of passpunkte) {
            let x = passpunkt.x * width
            let y = height - passpunkt.y * width
            let f = new Feature<Point>({
                geometry: new Point([x, y])
            })
            f.setProperties(passpunkt)
            this.punktLayerSource.addFeature(f)
        }
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

    private async refreshListe() {

        let liste = document.getElementById("passpunktListe");
        if (!liste) return
        liste.innerHTML = "";
        let pid = this.selectPasspunkt.value
        let passpunkte: PasspunktPosition[] = await fetch("/api/" + this.gui.projekt + "/passpunkte/" + pid + "/position").then((res) => res.json())
        for (let eintrag of passpunkte) {
            let c = document.createElement("canvas");
            let ctx = c.getContext("2d");
            if (!ctx) continue
            let image = new Image();
            image.src = "/api/" + this.gui.projekt + "/images/" + eintrag.image + "/file"
            image.onload = function () {
                if (!ctx) return
                let x = eintrag.x * image.width
                let y = eintrag.y * image.width
                ctx.drawImage(image, x - 50, y - 50, 100, 100, 0, 0, 100, 100);
                ctx.beginPath();
                ctx.moveTo(40, 50);
                ctx.lineTo(60, 50);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(50, 40);
                ctx.lineTo(50, 60);
                ctx.stroke();
            }
            c.addEventListener("click", () => {
                for (let b of this.bilder) {
                    if (eintrag.image == b.bid) {
                        this.bildauswahl(b)
                    }
                }

            })
            c.oncontextmenu = (e) => {
                e.preventDefault()
                this.deletePasspunktPosition(eintrag)
            }
            liste?.appendChild(c)
        }
    }

    private async deletePasspunktPosition(passpunkt: PasspunktPosition) {
        await fetch("/api/" + this.gui.projekt + "/passpunkte/" + passpunkt.passpunkt + "/" + passpunkt.image, {
            method: "DELETE"
        })
        this.refreshListe()
        this.loadPasspunktPosAufBild(passpunkt.image)
    }

    private async loadPasspunkte() {
        let passpunkte: Passpunkt[] = await fetch("/api/" + this.gui.projekt + "/passpunkte/").then((res) => res.json())
        this.selectPasspunkt.innerHTML = ""
        for (let p of passpunkte) {
            let option = document.createElement("option")
            option.value = p.pid.toString()
            option.innerHTML = p.name
            this.selectPasspunkt.appendChild(option)
        }
        this.selectPasspunkt.dispatchEvent(new Event("change"))
    }
}