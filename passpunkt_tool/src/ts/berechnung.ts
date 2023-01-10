import GUI from ".";
import Tool from "./tool";

export default class Berechnung extends Tool {
    start() { }
    stop() { }

    constructor(gui: GUI) {
        super(gui)
        document.getElementById("buttonFindSift")?.addEventListener("click", this.findSift.bind(this))
        document.getElementById("buttonMatchSift")?.addEventListener("click", this.matchSift.bind(this))
    }

    private async findSift() {
        await fetch("/api/" + this.gui.projekt + "/find_sift")
        alert("Fertig!")
    }

    private async matchSift() {
        await fetch("/api/" + this.gui.projekt + "/match_sift")
        alert("Fertig!")
    }
}