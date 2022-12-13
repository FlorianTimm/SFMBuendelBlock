import ImageLayer from 'ol/layer/Image';
import Map from 'ol/Map';
import Projection from 'ol/proj/Projection';
import Static from 'ol/source/ImageStatic';
import View from 'ol/View';
import { Extent, getCenter } from 'ol/extent';
import { MapBrowserEvent } from 'ol';
import { saveAs } from "file-saver";

import '../../node_modules/ol/ol.css'
import '../style/style.css';



function imageSize(url: string): Promise<{ width: number, height: number }> {
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

async function createSource(url: string): Promise<{ view: View; layer: Static; }> {
    let size = await imageSize(url)
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

const layer = new ImageLayer({})

const map = new Map({
    layers: [
        layer
    ],
    target: 'map',

});

type Passpunkt = {
    passpunkt: number,
    image: number,
    x: number,
    y: number
}

let passpunkte: Passpunkt[] = []

let passpunktNr = 0
let selectPasspunkt = <HTMLSelectElement>document.getElementById("passpunkt")
map.on("click", (e: MapBrowserEvent<any>) => {
    console.log(activeImage, e.coordinate, selectPasspunkt.value)
    if (parseInt(selectPasspunkt.value) == -1) {
        let neu = document.createElement("option")
        neu.value = (passpunktNr++).toString()
        neu.innerHTML = "Passpunkt " + neu.value
        selectPasspunkt.appendChild(neu)
        selectPasspunkt.selectedIndex = passpunktNr
    }
    passpunkte.push({
        passpunkt: parseInt(selectPasspunkt.value),
        image: activeImage,
        x: e.coordinate[0],
        y: e.coordinate[1]
    })
    refreshListe()
})
function refreshListe() {
    let liste = document.getElementById("passpunktListe");
    if (!liste) return
    liste.innerHTML = "";
    for (let eintrag of passpunkte) {
        if (eintrag.passpunkt != parseInt(selectPasspunkt.value)) continue
        let c = document.createElement("canvas");
        let ctx = c.getContext("2d");
        if (!ctx) continue
        let image = new Image();
        image.src = URL.createObjectURL(files[eintrag.image]);
        image.onload = function () {
            if (!ctx) return
            ctx.drawImage(image, eintrag.x - 50, image.height - eintrag.y - 50, 100, 100, 0, 0, 100, 100);
        }
        liste?.appendChild(c)
    }
}
selectPasspunkt.addEventListener("change", refreshListe)

const fileSelect = <HTMLInputElement>document.getElementById("OpenPicture")

let activeImage = -1
let files: File[] = []
fileSelect?.addEventListener("change", async () => {
    if (!fileSelect.files) return
    for (let file of fileSelect.files) {
        if (!file) return;
        files.push(file)

        let img = document.createElement('img')
        img.src = URL.createObjectURL(file)
        img.style.width = "90%"
        img.style.display = "block"
        let imgNr = files.length - 1
        document.getElementById("nav")?.appendChild(img)
        img.addEventListener("click", async () => {
            let daten = await createSource(img.src)
            layer.setSource(daten.layer);
            map.setView(daten.view)
            activeImage = imgNr
        })
    }
    if (files.length > 0) {
        let url = URL.createObjectURL(files[0])
        let daten = await createSource(url)
        layer.setSource(daten.layer);
        map.setView(daten.view)
        activeImage = 0
    }

    fileSelect.files = null

})


document.getElementById("speichern")?.addEventListener("click", () => {
    let exp: { bilder: string[], passpunkte: Passpunkt[] } = {
        bilder: [],
        passpunkte: passpunkte
    }
    for (let file of files) {
        exp.bilder.push(file.name)
    }
    let blob = new Blob([JSON.stringify(exp)], { type: "application/json" });
    saveAs(blob, "daten.json")
})