import GUI from ".";
import Tool from "./tool";

export default class Berechnung extends Tool {
    start() { }
    stop() { }

    constructor(gui: GUI) {
        super(gui)
        document.getElementById("buttonFindSift")?.addEventListener("click", this.findSift.bind(this))
        document.getElementById("buttonMatchSift")?.addEventListener("click", this.matchSift.bind(this))
        document.getElementById("buttonStartPair")?.addEventListener("click", this.startPair.bind(this))
        document.getElementById("buttonNextImage")?.addEventListener("click", this.nextImage.bind(this))
        document.getElementById("buttonNextCoordinates")?.addEventListener("click", this.nextCoordinates.bind(this))
        document.getElementById("buttonBundleBlock")?.addEventListener("click", this.bundleBlock.bind(this))
        document.getElementById("buttonExifDownload")?.addEventListener("click", this.exifDownload.bind(this))
    }

    private async findSift() {
        await fetch("/api/" + this.gui.projekt + "/find_sift")
        alert("Fertig!")
    }

    private async matchSift() {
        await fetch("/api/" + this.gui.projekt + "/match_sift")
        alert("Fertig!")
    }

    private async startPair() {
        await fetch("/api/" + this.gui.projekt + "/start_pair")
        alert("Fertig!")
    }

    private async nextImage() {
        await fetch("/api/" + this.gui.projekt + "/next_image")
        alert("Fertig!")
    }

    private async nextCoordinates() {
        await fetch("/api/" + this.gui.projekt + "/next_coordinates")
        alert("Fertig!")
    }

    private async bundleBlock() {
        await fetch("/api/" + this.gui.projekt + "/bundle_block")
        alert("Fertig!")
    }

    private async exifDownload() {
        await fetch("/api/" + this.gui.projekt + "/exif_download").then(response => response.text()).then(txt => {
            alert("Daten liegen unter " + txt)
        });
    }
}