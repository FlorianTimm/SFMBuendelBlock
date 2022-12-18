import sqlite3
import cv2
import numpy as np
import matplotlib.pyplot as plt


def find_sift(datenbank):
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
            good = []
            # ratio test as per Lowe's paper
            for k, (m, n) in enumerate(matches):
                if m.distance < 0.8*n.distance:
                    #liste[(j, m.trainIdx)] = (i, m.queryIdx)
                    good.append(m)

            paare = np.array([[m.queryIdx, m.trainIdx] for m in good])

            kp1 = np.array([n.pt for n in data[i]["kp"]])
            kp2 = np.array([n.pt for n in data[j]["kp"]])

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
            kp = data[id]['kp'][punkt]
            db.execute(
                "INSERT OR REPLACE INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)", (pid, data[id]["id"], kp.pt[0], kp.pt[1]))

    db.commit()
    cur.close()
    db.close()


def test(bilder, cur):
    img1 = cv2.imread(bilder[0][1])
    img2 = cv2.imread(bilder[1][1])

    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(
        cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY), None)
    kp2, des2 = sift.detectAndCompute(
        cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY), None)

    kp1 = np.array([n.pt for n in kp1])
    kp2 = np.array([n.pt for n in kp2])

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=100)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # Apply Lowe's SIFT matching ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good.append(m)

    paare = np.array([[m.queryIdx, m.trainIdx] for m in good])
    print(kp1[paare[:, 0]].T)

    # Constrain matches to fit homography
    retval, mask = cv2.findHomography(
        kp1[paare[:, 0]], kp2[paare[:, 1]], cv2.RANSAC, 100.0)
    mask = mask.ravel()

    # We select only inlier points
    paare = paare[mask == 1]
    print(kp1[paare[:, 0]].T)

    pts1 = kp1[paare[:, 0]].T
    pts2 = kp2[paare[:, 1]].T

    fig, ax = plt.subplots(1, 2)
    ax[0].autoscale_view('tight')
    ax[0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    ax[0].plot(pts1[0], pts1[1], 'r.')
    ax[1].autoscale_view('tight')
    ax[1].imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    ax[1].plot(pts2[0], pts2[1], 'r.')
    fig.show()
    plt.show()

    cur.execute("""DELETE FROM passpunktpos""")
    cur.execute("""DELETE FROM passpunkte""")

    for i, p in enumerate(paare):
        cur.execute("""INSERT INTO passpunkte (pid) VALUES (?)""", (i,))
        cur.execute(
            """INSERT INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)""", (i, bilder[0][0], kp1[p[0], 0], kp1[p[0], 1]))
        cur.execute(
            """INSERT INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?)""", (i, bilder[1][0], kp2[p[1], 0], kp2[p[1], 1]))


if __name__ == "__main__":
    print('Testdaten')
    find_sift('./example_data/bildverband2/datenbank.db')
