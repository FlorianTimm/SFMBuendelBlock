import sqlite3
import cv2
import numpy as np
import matplotlib.pyplot as plt


def find_sift(datenbank, width=600):
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
        "SELECT bid, pfad FROM bilder left join kameras on kamera = kid ORDER BY pfad DESC")
    bilder = cur.fetchall()

    sift = cv2.SIFT_create()

    data = []
    for bild in bilder:
        id, pfad = bild
        img = cv2.imread(pfad)
        scale_percent = width/img.shape[1]
        width = int(img.shape[1] * scale_percent)
        height = int(img.shape[0] * scale_percent)
        dim = (width, height)

        # resize image
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

        print(pfad)
        gray_image1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        kp, desc = sift.detectAndCompute(gray_image1, None)
        pt = np.array([np.array(n.pt)/gray_image1.shape[1]
                       for n in kp])
        data.append({"id": id, "kp": kp, "desc": desc, "pt": pt})

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=100)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    liste = {}
    for i in range(len(bilder)):
        for j in range(i+1, len(bilder)):
            matches = flann.knnMatch(data[i]["desc"], data[j]["desc"], k=2)
            good = []
            # ratio test as per Lowe's paper
            for k, (m, n) in enumerate(matches):
                if m.distance < 0.8*n.distance:
                    #liste[(j, m.trainIdx)] = (i, m.queryIdx)
                    good.append(m)

            paare = np.array([[m.queryIdx, m.trainIdx] for m in good])

            kp1 = data[i]["pt"]
            kp2 = data[j]["pt"]

            # Constrain matches to fit homography
            retval, mask = cv2.findHomography(
                kp1[paare[:, 0]], kp2[paare[:, 1]], cv2.RANSAC, 100.0)
            mask = mask.ravel()
            paare = paare[mask == 1]
            for p in paare:
                liste[(j, p[1])] = (i, p[0])

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
        cur.execute("INSERT OR IGNORE INTO passpunkte (name, type) VALUES (?, 'SIFT') RETURNING pid",
                    ('sift'+str(i),))
        pid = cur.fetchone()[0]
        for p in eintrag:
            id, punkt = p
            kp = data[id]['pt'][punkt]
            db.execute(
                "INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)", (pid, data[id]["id"], kp[0], kp[1]))

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    find_sift('./example_data/bildverband2/datenbank.db', 1000)
