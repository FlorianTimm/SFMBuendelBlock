import sqlite3
import cv2
import numpy as np
import matplotlib.pyplot as plt


class match_sift:
    def __init__(self, datenbank):
        self.datenbank = datenbank

    def match_sift(self, next_images=3, nearest_images=5):
        db = sqlite3.connect(self.datenbank)
        cur = db.cursor()
        cur.execute(
            "SELECT bid, pfad, x,y,z FROM bilder left join kameras on kamera = kid ORDER BY pfad DESC")
        bilder = cur.fetchall()

        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=100)
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        desc = []
        pt = []
        ids = []
        print("Lade Bilder")
        for bild in bilder:
            data1 = np.load(bild[1] + '.npz')
            desc.append(data1['desc'])
            pt.append(data1['pt'])
            ids.append(data1['id'])

        liste = {}
        for i in range(len(bilder)):
            cur.execute(
                """SELECT b.bid by FROM passpunktpos a, passpunktpos b WHERE a.pid = b.pid and a.bid = ? and b.bid > a.bid + ?""", (bilder[i][0], next_images))
            verkn = [z[0] for z in cur.fetchall()]
            for j in range(i+1, len(bilder)):
                dist = ((bilder[i][2]-bilder[j][2])**2+(bilder[i][3] -
                        bilder[j][3])**2+(bilder[i][4]-bilder[j][4])**2)**0.5

                if dist > nearest_images and j - i > next_images and bilder[j] not in verkn:
                    continue

                print(f"Vergleiche {i} mit {j}")

                matches = flann.knnMatch(desc[i], desc[j], k=2)
                good = []
                # ratio test as per Lowe's paper
                for k, (m, n) in enumerate(matches):
                    if m.distance < 0.8*n.distance:
                        #liste[(j, m.trainIdx)] = (i, m.queryIdx)
                        good.append(m)

                paare = np.array([[m.queryIdx, m.trainIdx] for m in good])

                # Constrain matches to fit homography
                retval, mask = cv2.findHomography(
                    pt[i][paare[:, 0]], pt[j][paare[:, 1]], cv2.RANSAC, 100.0)
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
                db.execute(
                    "INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)", (int(pid), int(bilder[id][0]), pt[id][punkt][0], pt[id][punkt][1]))

        db.commit()
        cur.close()
        db.close()


if __name__ == "__main__":
    print('Testdaten')
    match_sift('./example_data/heilgarten.db')
