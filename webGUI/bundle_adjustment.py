from scipy.sparse import lil_matrix
from scipy.optimize import least_squares
import sqlite3
import numpy as np
import cv2
import matplotlib.pyplot as plt
from numpy.typing import NDArray

num_bild_param = 6
num_cam_param = 4
num_pass_param = 3


def bundle_adjustment(datenbank: str) -> None:
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute(
        """SELECT kid, fx, fy, x0, y0 FROM kameras WHERE kid in (SELECT distinct kamera FROM bilder WHERE lx IS NOT NULL)""")
    kamera = np.array(cur.fetchall())
    kamera_ids = np.array(kamera[:, 0], dtype=np.int32)

    cur.execute(
        """SELECT bid, kamera, lx, ly, lz, lrx, lry, lrz FROM bilder WHERE lx IS NOT NULL""")
    bilder = np.array(cur.fetchall())
    bilder_ids = np.array(bilder[:, :2], dtype=np.int32)

    cur.execute(
        """SELECT pid, lx, ly, lz from passpunkte WHERE lx IS NOT NULL""")
    passpunkte = np.array(cur.fetchall())
    passpunkte_ids = np.array(passpunkte[:, 0], dtype=np.int32)

    cur.execute("""SELECT ppid, pid, bid, x, y FROM passpunktpos WHERE pid in (SELECT pid from passpunkte WHERE lx IS NOT NULL) AND bid in (SELECT bid FROM bilder WHERE lx IS NOT NULL)""")
    messung = np.array(cur.fetchall())
    messung_ids = np.array(messung[:, :3], dtype=np.int32)

    l = np.array(messung[:, -2:].ravel(), dtype=np.float64)

    x0 = np.hstack((kamera[:, 1:].ravel(),
                   bilder[:, 2:].ravel(), passpunkte[:, 1:].ravel()))

    A = lil_matrix((len(l), len(x0)), dtype=int)

    n_camera = len(kamera)
    n_bilder = len(bilder)
    n_passpunkte = len(passpunkte)
    n_messungen = len(messung)
    messung_bild_id = np.empty(n_messungen, dtype=np.int32)
    messung_kamera_id = np.empty(n_messungen, dtype=np.int32)
    messung_passpunkt_id = np.empty(n_messungen, dtype=np.int32)

    for i, m in enumerate(messung):
        bild_id, = np.where(bilder_ids[:, 0] == m[2])
        bild_id = bild_id[0]
        messung_bild_id[i] = bild_id

        camera_id_array,  = np.where(kamera_ids[:] == bilder[bild_id, 1])
        camera_id = camera_id_array[0]
        messung_kamera_id[i] = camera_id

        passpunkt_id, = np.where(passpunkte_ids[:] == m[1])
        passpunkt_id = passpunkt_id[0]
        messung_passpunkt_id[i] = passpunkt_id

        offset = camera_id*num_cam_param
        A[2*i:2*i+2, offset:offset+num_cam_param] = 1

        offset = n_camera * num_cam_param + bild_id * num_bild_param
        A[2*i:2*i+2, offset:offset + num_bild_param] = 1

        offset = n_camera*num_cam_param + n_bilder * \
            num_bild_param + passpunkt_id * num_pass_param
        A[2*i:2*i+2, offset:offset + num_pass_param] = 1

    def project(x0: NDArray[np.float32]) -> NDArray[np.float32]:
        p = np.empty(len(l), dtype=np.float32)

        K = []
        for i in range(n_camera):
            offset = i * num_cam_param
            fx = x0[offset]
            fy = x0[offset + 1]
            cx = x0[offset + 2]
            cy = x0[offset + 3]
            K.append(np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]))

        r = []
        t = []
        for i in range(n_bilder):
            offset = n_camera * num_cam_param + \
                i*num_bild_param

            t.append(x0[offset:offset+3])
            r.append(x0[offset+3:offset+6])

        X = []
        for i in range(n_passpunkte):
            offset = n_camera * num_cam_param + \
                n_bilder*num_bild_param + \
                num_pass_param * i
            X.append(x0[offset:offset+3].reshape(1, 3))

        for i, m in enumerate(messung):
            punkt, _ = cv2.projectPoints(
                X[messung_passpunkt_id[i]], r[messung_bild_id[i]], t[messung_bild_id[i]], K[messung_kamera_id[i]], None)
            # print(i*2+1)
            p[i*2] = punkt[0, 0, 0]
            p[i*2+1] = punkt[0, 0, 1]

        return p.ravel()-l

    res = least_squares(project, x0, jac_sparsity=A, verbose=2,
                        x_scale='jac', method='trf', ftol=1e-3)  # type: ignore
    """
    print(res.x)


    coords_new = res.x[n_camera * num_cam_param +
                       n_bilder*num_bild_param:]
    coords_new = coords_new.reshape(len(coords_new)//3, 3)

    fig = plt.figure()
    fig.suptitle('3D reconstructed', fontsize=16)
    ax = fig.add_subplot(projection='3d')
    ax.plot(coords_new.T[0], coords_new.T[1], coords_new.T[2], 'r.')
    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')
    ax.view_init(elev=135, azim=90)
    plt.axis('square')
    ax.set_ylim([-1, 2])
    ax.set_xlim([-1, 2])
    ax.set_zlim([-1, 2])
    plt.show()
    """
    x = res.x

    cur.executemany("""UPDATE kameras SET fx = ?, fy = ?, x0 = ?, y0 = ? WHERE kid = ?""",
                    np.c_[x[:num_cam_param * n_camera].reshape(n_camera, num_cam_param), kamera_ids])

    offset = num_cam_param * n_camera
    cur.executemany("""UPDATE bilder SET lx = ?, ly = ?, lz = ?, lrx = ?, lry = ?, lrz = ? WHERE bid = ?""",
                    np.c_[x[offset:offset+num_bild_param*n_bilder].reshape(n_bilder, num_bild_param), bilder_ids[:, 0]])

    offset = offset+num_bild_param*n_bilder
    cur.executemany("""UPDATE passpunkte SET lx = ?, ly = ?, lz = ? WHERE pid = ?""",
                    np.c_[x[offset:offset+num_pass_param*n_passpunkte].reshape(n_passpunkte, num_pass_param), passpunkte_ids])

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    bundle_adjustment(
        './example_data/heilgarten.db')
