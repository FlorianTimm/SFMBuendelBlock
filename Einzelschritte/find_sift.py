import sqlite3
import cv2
import numpy as np
import matplotlib.pyplot as plt


def find_sift(datenbank, soll_width=600):
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
    db.commit()
    cur.close()
    db.close()

    sift = cv2.SIFT_create()

    data = []
    for bild in bilder:
        id, pfad = bild
        img = cv2.imread(pfad)
        scale_percent = soll_width/img.shape[1]
        width = int(img.shape[1] * scale_percent)
        height = int(img.shape[0] * scale_percent)
        dim = (width, height)

        # resize image
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

        print(pfad)
        gray_image1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        kp, desc = sift.detectAndCompute(gray_image1, None)

        pt = np.array([n.pt for n in kp])/soll_width
        print(desc.shape, pt.shape)
        np.savez_compressed(pfad + '.npz', id=id, desc=desc, pt=pt)


if __name__ == "__main__":
    print('Testdaten')
    find_sift('./example_data/heilgarten.db', 1000)
