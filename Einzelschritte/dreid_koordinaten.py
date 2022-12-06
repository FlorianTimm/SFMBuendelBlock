import math
import sqlite3
import numpy as np
import cv2 as cv
from naeherungswerte import get_kameramatrix
from etc import eulerAnglesToRotationMatrix
from etc import rotationMatrixToEulerAngles


def dreid_koordinaten(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS passpunkt_koords (
        pid INTEGER REFERENCES passpunkte(pid),
        lx NUMBER,
        ly NUMBER,
        lz NUMBER
    )""")

    cur.execute(
        "SELECT a.bid, a.lx, a.ly, a.lz, a.lrx, a.lry, a.lrz, b.bid, b.lx, b.ly, b.lz, b.lrx, b.lry, b.lrz FROM bildpaare JOIN bilder a ON a.bid = bid1 JOIN bilder b ON b.bid = bid2")
    paare = cur.fetchall()
    for bid1, x1, y1, z1, rx1, ry1, rz1, bid2, x2, y2, z2, rx2, ry2, rz2 in paare:
        R1 = eulerAnglesToRotationMatrix(rx1, ry1, rz1)
        R2 = eulerAnglesToRotationMatrix(rx2, ry2, rz2)
        Rt1 = np.c_[R1, np.array([x1, y1, z1])]
        # np.append(### , np.array( [0, 0, 0, 1])).reshape(4, 4)
        Rt2 = np.c_[R2, np.array([x2, y2, z2])]
        # np.append(### , np.array( [0, 0, 0, 1])).reshape(4, 4)
        K = get_kameramatrix(cur, 1)

        P1 = K@Rt1
        P2 = K@Rt2

        cur.execute(
            """SELECT a.pid, a.x, a.y, b.x, b.y FROM passpunktpos a, passpunktpos b WHERE a.pid = b.pid and a.bid = ? and b.bid = ?""", (bid1, bid2))
        daten = np.array(cur.fetchall())
        pid = daten[:, 0]
        pts1 = daten[:, 1:3]
        pts2 = daten[:, 3:5]
        points_3d = cv.triangulatePoints(P1, P2, pts1.T, pts2.T)
        points_3d /= points_3d[3]
        punkte = zip(pid, points_3d[0], points_3d[1], points_3d[2])
        cur.executemany(
            """INSERT INTO passpunkt_koords (pid, lx, ly, lz) VALUES (?,?,?,?)""", punkte)

    # cur.execute("""ALTER TABLE passpunkte ADD COLUMN lx NUMBER""")
    # cur.execute("""ALTER TABLE passpunkte ADD COLUMN ly NUMBER""")
    # cur.execute("""ALTER TABLE passpunkte ADD COLUMN lz NUMBER""")

    cur.execute("""ALTER TABLE passpunkte ADD COLUMN lx NUMBER""")
    cur.execute("""ALTER TABLE passpunkte ADD COLUMN ly NUMBER""")
    cur.execute("""ALTER TABLE passpunkte ADD COLUMN lz NUMBER""")

    cur.execute("""UPDATE passpunkte SET lx = upd.lx, ly = upd.ly, lz = upd.lz FROM (SELECT pid,
            avg(lx) lx,
            avg(ly) ly,
            avg(lz) lz
        FROM passpunkt_koords
        group by pid) upd WHERE upd.pid = passpunkte.pid;""")

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    dreid_koordinaten(
        './Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
