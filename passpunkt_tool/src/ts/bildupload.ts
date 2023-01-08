import GUI from ".";
import Tool from "./tool";

export default class BildUpload extends Tool {
    private fileSelect: HTMLInputElement;
    bilderListe: HTMLTableElement;

    constructor(gui: GUI) {
        super(gui)
        this.fileSelect = <HTMLInputElement>document.getElementById("OpenPicture")
        this.fileSelect?.addEventListener("change", this.fileUpload.bind(this))
        this.bilderListe = <HTMLTableElement>document.getElementById("bilderliste")
    }

    async start() {
        console.log("Bilder-Tool gestartet")
        this.bilderListe.innerHTML = ""
        let bilder = await fetch("/api/" + this.gui.projekt + "/images/").then((res) => res.json())
        for (let bild of bilder) {
            let tr = document.createElement("tr")
            for (let e of bild) {
                let td = document.createElement("td")
                td.innerText = e
                tr.appendChild(td)
            }
            this.bilderListe.appendChild(tr)
        }
    }

    stop() {

    }

    async fileUpload() {
        if (!this.fileSelect.files) return

        let uploads: Promise<Response>[] = []
        for (let file of this.fileSelect.files) {
            let data = new FormData()
            data.append("file", file)
            uploads.push(
                fetch('/api/' + this.gui.projekt + '/images/', {
                    method: 'POST',
                    body: data
                })
            )
        }
        await Promise.all(uploads)

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
        }
*/
        this.fileSelect.files = null

    }
}