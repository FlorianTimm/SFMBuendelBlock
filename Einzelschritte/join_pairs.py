import math
import sqlite3
import numpy as np
from etc import eulerAnglesToRotationMatrix
from etc import rotationMatrixToEulerAngles


def join_pairs(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsx NUMBER""")
    cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsy NUMBER""")
    cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsz NUMBER""")
    cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsdist NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN lx NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN ly NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN lz NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN lrx NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN lry NUMBER""")
    cur.execute("""ALTER TABLE bilder ADD COLUMN lrz NUMBER""")

    cur.execute(
        """UPDATE bildpaare SET gpsx = d.gpsx, gpsy = d.gpsy, gpsz = d.gpsz FROM (
        SELECT bild1.bid bid1, bild2.bid bid2,
            bild2.x-bild1.x gpsx,
            bild2.y-bild1.y gpsy,
            bild2.z-bild1.z gpsz FROM bilder bild1, bilder bild2) d WHERE bildpaare.bid1 = d.bid1 AND bildpaare.bid2 = d.bid2""")
    cur.execute(
        """UPDATE bildpaare SET gpsdist = sqrt(gpsx*gpsx+gpsy
        *gpsy+gpsz*gpsz)""")

    cur.execute("""SELECT bids.bid, count(*)
    FROM (
            SELECT bid1 bid
            FROM bildpaare
            UNION ALL
            SELECT bid2 bid
            FROM bildpaare
        ) bids
    GROUP BY bids.bid
    ORDER BY COUNT(*) DESC
    LIMIT 1""")

    startbild, _ = cur.fetchone()

    cur.execute(
        """UPDATE bilder SET lx = NULL, ly = NULL, lz = NULL, lrx = NULL, lry = NULL, lrz  = NULL""")
    cur.execute(
        """UPDATE bilder SET lx = 0, ly = 0, lz = 0, lrx = 0, lry = 0, lrz  = 0 WHERE bid = ?""", (startbild,))

    while True:
        cur.execute("""WITH paare as (
    SELECT bid1,
        bid2
    FROM bildpaare
    UNION
    SELECT bid2 bid1,
        bid1 bid2
    FROM bildpaare
),
meiste AS (
    SELECT bid2
    FROM paare
        JOIN bilder von ON bid1 = von.bid
        JOIN bilder bis ON bid2 = bis.bid
    WHERE von.lx IS NOT NULL
        AND bis.lx IS NULL
    GROUP BY bid2
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
SELECT meiste.bid2 = p.bid1,
    meiste.bid2,
    von.lx lx1,
    von.ly ly1,
    von.lz lz1,
    von.lrx lrx1,
    von.lry lry1,
    von.lrz lrz1,
    p.lx lx2,
    p.ly ly2,
    p.lz lz2,
    p.lrx lrx2,
    p.lry lry2,
    p.lrz lrz2,
    gpsdist
FROM meiste
    JOIN bildpaare p ON meiste.bid2 = p.bid1 OR meiste.bid2 = p.bid2
    JOIN bilder von ON von.lx IS NOT NULL AND von.bid != meiste.bid2 AND von.bid  IN (p.bid1,p.bid2)""")
        bid = None
        werte = []
        for drehen, bid, lx1, ly1, lz1, lrx1, lry1, lrz1, lx2, ly2, lz2, lrx2, lry2, lrz2, gpsdist in cur.fetchall():
            R1 = eulerAnglesToRotationMatrix(lrx1, lry1, lrz1)
            R2 = eulerAnglesToRotationMatrix(lrx2, lry2, lrz2)
            t1 = np.array([lx1, ly1, lz1])
            t2 = np.array([lx2, ly2, lz2])

            if not drehen:
                t = t1 + R1@t2*gpsdist
                R = R2@R1
            else:
                t = t1-np.linalg.inv(R2)@R1@t2*gpsdist
                R = np.linalg.inv(R2)@R1
            rx, ry, rz = rotationMatrixToEulerAngles(R)
            print(bid, rx, ry, rz)
            werte.append([t[0], t[1],  t[2], rx, ry, rz, bid])
        if len(werte) > 0:
            if (len(werte) > 1):
                werte = np.array(werte)
                t = np.mean(werte[:, :3], axis=0)
                rx = winkel_mitteln(list(werte[:, 3]))
                ry = winkel_mitteln(list(werte[:, 4]))
                rz = winkel_mitteln(list(werte[:, 5]))
                werte = [t[0], t[1], t[2], rx, ry, rx, werte[0, 6]]
                print(bid, rx, ry, rz)
            else:
                werte = werte[0]
            werte = tuple(werte)
            cur.execute(
                """UPDATE bilder SET lx = ?, ly = ?, lz = ?, lrx = ?, lry = ?, lrz = ? WHERE bid = ?""", werte)

        else:
            break

    db.commit()
    cur.close()
    db.close()


def winkel_mitteln(werte: list):
    sumC = 0
    sumS = 0
    count = 0
    for e in werte:
        sumC += math.cos(e)
        sumS += math.sin(e)
        count += 1
    l = (sumC**2 + sumS**2)**0.5
    return math.atan2(sumS, sumC)


if __name__ == "__main__":
    print('Testdaten')
    join_pairs('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
