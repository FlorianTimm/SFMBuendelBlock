import cv2
import sqlite3
import numpy as np
from naeherungswerte import get_kameramatrix, reconstruct_one_point, cart2hom


def join_nextpictures(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""SELECT b.bid, kamera FROM bilder b
        JOIN passpunktpos pp ON pp.bid = b.bid
        JOIN passpunkte p ON pp.pid = p.pid
        WHERE b.lx IS NULL AND p.lx is not null group by b.bid  HAVING COUNT(*) > 4 order by count(*) DESC LIMIT 1""")

    bid, kid = cur.fetchone()

    cur.execute("""SELECT pp.x, pp.y, lx, ly, lz FROM passpunktpos pp
        JOIN passpunkte p ON pp.pid = p.pid
        WHERE pp.bid = ? AND p.lx is not null""", (bid, ))

    passpunkte = np.array(cur.fetchall())

    K = get_kameramatrix(cur, bid)

    _, r, t, _ = cv2.solvePnPRansac(
        passpunkte[:, 2:], passpunkte[:, :2],  K, None)

    cur.execute("UPDATE bilder SET lx = ?, ly = ?, lz = ?, lrx = ?, lry = ?, lrz = ? WHERE bid = ?;",
                (float(t[0]), float(t[1]), float(t[2]), float(r[0]), float(r[1]), float(r[2]), int(bid)))

    print(r, t)

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    join_nextpictures('./example_data/bildverband2/datenbank.db')
