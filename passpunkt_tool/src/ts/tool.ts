import GUI from ".";

export default abstract class Tool {
    protected gui: GUI
    static _tools: Tool[] = []

    public static get tools() {
        return Tool._tools
    }

    protected constructor(gui: GUI) {
        this.gui = gui;
        Tool._tools.push(this)
    }

    abstract start(): void;
    abstract stop(): void;
}