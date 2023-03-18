import sqlite3
import cv2
import numpy as np
import matplotlib.pyplot as plt
from create_database import create_database
from typing import List, Tuple


class find_sift():

    def __init__(self, datenbank: str, soll_width: int = 600):
        self.datenbank = datenbank
        self.soll_width = soll_width
        self.sift = cv2.SIFT_create()

    def find_sift_in_image(self, image: Tuple[int, str]) -> None:
        id, pfad = image
        img = cv2.imread(pfad)
        scale_percent = self.soll_width/img.shape[1]
        width = int(img.shape[1] * scale_percent)
        height = int(img.shape[0] * scale_percent)
        dim = (width, height)

        # resize image
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

        print(pfad)
        gray_image1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        kp, desc = self.sift.detectAndCompute(gray_image1, None)

        pt = np.array([n.pt for n in kp])/self.soll_width
        np.savez_compressed(pfad + '.npz', id=id, desc=desc, pt=pt)

    def find_sift_in_all(self) -> None:
        db = sqlite3.connect(self.datenbank)
        cur = db.cursor()
        cur.execute(
            "SELECT bid, pfad FROM bilder left join kameras on kamera = kid ORDER BY pfad DESC")
        bilder: List[Tuple[int, str]] = cur.fetchall()
        cur.close()
        db.close()

        for bild in bilder:
            self.find_sift_in_image(bild)


if __name__ == "__main__":
    print('Testdaten')
    find_sift('./example_data/heilgarten.db', 1000)
