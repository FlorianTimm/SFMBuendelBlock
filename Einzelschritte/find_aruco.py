import sqlite3
import cv2
from cv2 import aruco
import numpy as np


def find_aruco(datenbank):
    db = sqlite3.connect(datenbank)
    db.execute("""CREATE TABLE IF NOT EXISTS passpunkte (
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            x NUMBER,
            y NUMBER,
            z NUMBER,
            lx NUMBER,
            ly NUMBER,
            lz NUMBER
            )""")
    db.execute("""CREATE TABLE IF NOT EXISTS passpunktpos (
            ppid INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER REFERENCES passpunkte(pid),
            bid INTEGER REFERENCES bilder(bid),
            x NUMBER,
            y NUMBER,
            UNIQUE (pid, bid))""")

    cur = db.cursor()
    cur.execute(
        "SELECT bid, pfad FROM bilder left join kameras on kamera = kid")
    bilder = cur.fetchall()

    LUT_IN = [0, 158, 216, 255]
    LUT_OUT = [0, 22, 80, 176]
    lut = np.interp(np.arange(0, 256),
                    LUT_IN, LUT_OUT).astype(np.uint8)

    aruco_dict = aruco.Dictionary_create(32, 3)

    markers = set()
    for bild in bilder:
        id, pfad = bild
        cv_img = cv2.imread(pfad)
        tmp = cv2.LUT(cv_img, lut)
        gray = cv2.cvtColor(tmp, cv2.COLOR_BGR2GRAY)

        parameter = aruco.DetectorParameters.create()
        parameter.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
        corners, ids, _ = aruco.detectMarkers(
            gray, aruco_dict, parameters=parameter)

        for nr in range(len(ids)):
            for cid in range(len(corners[nr][0])):
                name = 'aruco' + str(ids[nr][0]) + '-' + str(cid)
                x = float(corners[nr][0][cid][0])
                y = float(corners[nr][0][cid][1])
                db.execute("INSERT OR IGNORE INTO passpunkte (name, type) VALUES (?, 'aruco')",
                           (name,))
                db.execute("INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES ((SELECT pid FROM passpunkte WHERE name = ?),?,?,?)",
                           (name, id, x, y))

        # marked = aruco.drawDetectedMarkers(cv_img, corners, ids)
        # cv2.imshow('image', cv2.resize(marked, (800,600)))
        # cv2.waitKey(0)
    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    find_aruco('./example_data/bildverband2/datenbank.db')
