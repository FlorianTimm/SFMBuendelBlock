import '../../node_modules/ol/ol.css'
import '../style/style.css';
import Berechnung from './berechnung';
import BildUpload from './bildupload';
import DreiD from './dreid';
import PasspunktTool from './passpunkte';
import Tool from './tool';

export default class GUI {
    private _projekt = "";

    public get projekt() {
        return this._projekt;
    }

    constructor() {
        let selectProjekt: HTMLSelectElement = <HTMLSelectElement>document.getElementById("selectProjekt")
        if (!selectProjekt) throw "Fehler"

        fetch("/api/").then(async (res: Response) => {
            let liste = await res.json()
            for (let eintrag of liste) {
                let e = document.createElement("option")
                e.innerHTML = eintrag;
                e.value = eintrag;
                selectProjekt.appendChild(e)
            }
            selectProjekt.dispatchEvent(new Event('change'))
        })


        selectProjekt.addEventListener("change", () => {
            this._projekt = selectProjekt.value
            this.show("bilder", bild_upload)
        })

        let passpunkt_tool = new PasspunktTool(this)
        let bild_upload = new BildUpload(this)
        let berechnung = new Berechnung(this)
        let dreid = new DreiD(this)


        document.getElementById("buttonBilder")?.addEventListener("click", () => this.show("bilder", bild_upload))
        document.getElementById("buttonPasspunkte")?.addEventListener("click", () => this.show("passpunkte", passpunkt_tool))
        document.getElementById("button3D")?.addEventListener("click", () => this.show("dreid", dreid))
        document.getElementById("buttonBerechnung")?.addEventListener("click", () => this.show("berechnung", berechnung))

        document.getElementById("neuesProjekt")?.addEventListener("click", this.neuesProjekt.bind(this))

        //this.show("bilder", bild_upload)
    }

    private neuesProjekt() {
        let name = prompt("Projektname")
        fetch("/api/" + name, { method: 'PUT' })
    }

    private show(id: string, tool: Tool) {
        for (let t of document.getElementsByClassName("tool")) {
            let ele = <HTMLElement>t
            ele.style.display = "none"
        }
        for (let t of Tool.tools) {
            if (t !== tool)
                t.stop()
        }
        tool.start()
        let s = document.getElementById(id)
        if (s) s.style.display = "inherit"
    }
}

new GUI()