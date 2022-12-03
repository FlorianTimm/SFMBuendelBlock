import sqlite3
import cv2
import numpy as np


def find_sift(datenbank):
    db = sqlite3.connect(datenbank)
    db.execute("""CREATE TABLE IF NOT EXISTS passpunkte (
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            x NUMBER,
            y NUMBER,
            z NUMBER
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

    sift = cv2.SIFT_create()

    data = []
    for bild in bilder:
        id, pfad = bild
        image1 = cv2.imread(pfad)
        print(pfad)
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        kp, desc = sift.detectAndCompute(gray_image1, None)
        data.append({"id": id, "kp": kp, "desc": desc})

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=100)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    liste = {}
    for i in range(len(bilder)):
        for j in range(i+1, len(bilder)):
            matches = flann.knnMatch(data[i]["desc"], data[j]["desc"], k=2)

            # ratio test as per Lowe's paper
            for k, (m, n) in enumerate(matches):
                if m.distance < 0.7*n.distance:
                    liste[(j, m.trainIdx)] = (i, m.queryIdx)

    # Suche Tracks
    gruppen = []
    for key in liste.keys():
        unterliste = []
        unterliste.append(key)
        while True:
            wert = liste[key]
            unterliste.append(wert)
            if wert in liste:
                key = wert
            else:
                break
        gruppen.append(unterliste)

    for i, eintrag in enumerate(gruppen):
        cur.execute("INSERT OR IGNORE INTO passpunkte (name) VALUES (?) RETURNING pid",
                    ('sift'+str(i),))
        pid = cur.fetchone()[0]
        for p in eintrag:
            id, punkt = p
            kp = data[id]['kp'][punkt]
            db.execute(
                "INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)", (pid, data[id]["id"], kp.pt[0], kp.pt[1]))

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    find_sift('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
