import sqlite3
import cv2
from cv2 import aruco as cv2_aruco
import numpy as np


class aruco:
    def create_tables(db):
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
        db.commit()

    def create_from_db_path(datenbank):
        return aruco(sqlite3.connect(datenbank))

    def __init__(self, db):
        self.db = db

        LUT_IN = [0, 158, 216, 255]
        LUT_OUT = [0, 22, 80, 176]
        self.lut = np.interp(np.arange(0, 256),
                             LUT_IN, LUT_OUT).astype(np.uint8)

        self.aruco_dict = cv2_aruco.Dictionary_create(32, 3)

        self.parameter = cv2_aruco.DetectorParameters.create()
        self.parameter.cornerRefinementMethod = cv2_aruco.CORNER_REFINE_SUBPIX

        aruco.create_tables(self.db)

    def find_markers(self, id, pfad):
        cv_img = cv2.imread(pfad)
        tmp = cv2.LUT(cv_img, self.lut)
        gray = cv2.cvtColor(tmp, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2_aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.parameter)
        try:
            for nr in range(len(ids)):
                for cid in range(len(corners[nr][0])):
                    name = 'aruco' + str(ids[nr][0]) + '-' + str(cid)
                    x = float(corners[nr][0][cid][0]) / cv_img.shape[1]
                    y = float(corners[nr][0][cid][1]) / cv_img.shape[1]
                    self.db.execute("INSERT OR IGNORE INTO passpunkte (name, type) VALUES (?, 'aruco')",
                                    (name,))
                    self.db.execute("INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES ((SELECT pid FROM passpunkte WHERE name = ?),?,?,?)",
                                    (name, id, x, y))
        except:
            pass
        self.db.commit()
        return

    def find_all_aruco(self):
        cur = self.db.cursor()
        cur.execute(
            "SELECT bid, pfad FROM bilder")
        bilder = cur.fetchall()

        for bild in bilder:
            id, pfad = bild
            self.find_markers(id, pfad)

        self.db.commit()
        cur.close()


"""
    def __del__(self):
        self.db.commit()
        # self.db.close()
"""

if __name__ == "__main__":
    print('Testdaten')
    a = aruco.create_from_db_path('./example_data/bildverband2/datenbank.db')
    a.find_all_aruco()
