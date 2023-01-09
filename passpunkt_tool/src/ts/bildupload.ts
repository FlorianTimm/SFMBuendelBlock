import GUI from ".";
import Tool from "./tool";
import { Bild } from "./types";

export default class BildUpload extends Tool {
    private fileSelect: HTMLInputElement;
    bilderListe: HTMLTableElement;

    constructor(gui: GUI) {
        super(gui)
        this.fileSelect = <HTMLInputElement>document.getElementById("OpenPicture")
        this.fileSelect?.addEventListener("change", this.fileUpload.bind(this))
        this.bilderListe = <HTMLTableElement>document.getElementById("bilderliste")

        document.getElementById("searchAruco")?.addEventListener("click", async () => {
            await fetch("/api/" + this.gui.projekt + "/find_aruco")
            alert("Fertig!")
        })
    }

    async start() {
        console.log("Bilder-Tool gestartet")
        this.bilderListe.innerHTML = ""
        let bilder: Bild[] = await fetch("/api/" + this.gui.projekt + "/images/").then((res) => res.json())
        for (let bild of bilder) {
            let tr = document.createElement("tr")
            for (let e of ["<img src=\"" + bild.url + "\" />", bild.bid, bild.kamera]) {
                let td = document.createElement("td")
                td.innerHTML = '' + e
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

        this.fileSelect.files = null

    }
}