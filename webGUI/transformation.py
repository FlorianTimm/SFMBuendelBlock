from sqlite3 import connect
import numpy as np
from numpy.typing import NDArray


class transformation:
    def __init__(self, datenbank_pfad: str):
        self.db = connect(datenbank_pfad)
        self.cursor = self.db.cursor()

    def calc_parameters(self) -> tuple[NDArray[np.float64], float, NDArray[np.float64]]:
        self.cursor.execute(
            "SELECT x,y,z,lx,ly,lz FROM bilder WHERE x is NOT NULL and lx is NOT NULL UNION SELECT x,y,z,lx,ly,lz FROM passpunkte WHERE x is NOT NULL and lx is NOT NULL ")
        punkte = np.array(self.cursor.fetchall(), dtype=np.float64)
        globale = punkte[:, :3]
        lokale = punkte[:, 3:]

        print(globale)
        print(lokale)

        # Schwerpunkte
        mean_g = np.mean(globale, axis=0)
        mean_l = np.mean(lokale, axis=0)

        t = mean_g - mean_l

        # Reduktion auf Schwerpunkt
        glob_m = globale - mean_g
        loka_m = lokale - mean_l

        laenge_g = 0.
        laenge_l = 0.

        # Gesamtlänge
        for i in range(len(glob_m)):
            laenge_g += float(np.linalg.norm(glob_m[i]))
            laenge_l += float(np.linalg.norm(loka_m[i]))

        # Maßstab
        s = laenge_g / laenge_l

        loka_m = loka_m * s

        # TODO Rotationsmatrix: loka_m * R = glob_m

        R = np.eye(3)  # TODO Berechnung

        return t, s, R

    def __del__(self) -> None:
        self.cursor.close()
        self.db.close()
