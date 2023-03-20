from sqlite3 import connect
import numpy as np
from numpy.typing import NDArray
from cv2 import Rodrigues


class transformation:
    def __init__(self, datenbank_pfad: str):
        self.db = connect(datenbank_pfad)
        self.cursor = self.db.cursor()
        self.r = np.zeros((3, 4))
        self.r[0, 0] = 1
        self.r[1, 1] = 1
        self.r[2, 2] = 1

    def calc_parameters(self) -> NDArray[np.float64]:
        self.cursor.execute(
            "SELECT x,y,z,lx,ly,lz FROM bilder WHERE x is NOT NULL and lx is NOT NULL UNION SELECT x,y,z,lx,ly,lz FROM passpunkte WHERE x is NOT NULL and lx is NOT NULL ")
        punkte = np.array(self.cursor.fetchall(), dtype=np.float64)
        globale = punkte[:, :3]
        lokale = punkte[:, 3:]

        l = globale.ravel()

        A = np.zeros((len(l), 12))

        for p in range(len(lokale)):
            for i in range(3):
                A[p*3+i, i*4:i*4+3] = lokale[p].T
                A[p*3+i, i*4+3] = 1

        N = A.T @ A
        x = np.linalg.inv(N) @ A.T @ l

        self.r = x.reshape((3, 4))
        print("Rotation: ", self.r[:, :3])
        print("Translation ", self.r[:, 3:])
        return self.r

    def transform_points(self) -> None:
        self.cursor.execute(
            "SELECT lx,ly,lz,lrx,lry,lrz, bid FROM bilder WHERE lx is NOT NULL")
        bilder = np.array(self.cursor.fetchall())

        bilder[:, 0:3] = (
            self.r @ np.c_[bilder[:, 0:3], np.ones(len(bilder))].T).T

        for i in range(len(bilder)):
            lrx, lry, lrz = bilder[i, 3:6]
            r = self.r[:, :3] @ Rodrigues(np.array([lrx, lry,
                                                    lrz], dtype=np.float32))[0]
            Rodrigues(r, bilder[i, 3:6])

        self.cursor.executemany(
            "UPDATE bilder SET x=?,y=?,z=?,rx=?,ry=?,rz=? WHERE bid=?", bilder)

        self.cursor.execute(
            "SELECT lx, ly, lz,pid FROM passpunkte WHERE lx is NOT NULL ")
        punkte = np.array(self.cursor.fetchall())
        punkte[:, 0:3] = (
            self.r @ np.c_[punkte[:, 0:3], np.ones(len(punkte))].T).T

        self.cursor.executemany(
            "UPDATE passpunkte SET x=?,y=?,z=? WHERE pid=?", punkte)

        self.db.commit()

    def __del__(self) -> None:
        self.cursor.close()
        self.db.close()
