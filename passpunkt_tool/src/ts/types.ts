export type Bild = {
    bid: number,
    width: number,
    height: number,
    kamera: number,
    url: string,
    x?: number,
    y?: number,
    z?: number,
    rx?: number,
    ry?: number,
    rz?: number
}

export type PasspunktPosition = {
    name?: string,
    passpunkt: number,
    image: number,
    x: number,
    y: number
}

export type Passpunkt = {
    name: string,
    pid: number,
    type: "manual" | "aruco" | "sift",
    x?: number,
    y?: number,
    z?: number
}