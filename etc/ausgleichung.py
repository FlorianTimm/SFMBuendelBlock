import sqlite3
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from scipy.spatial.transform import Rotation

from etc import eulerAnglesToRotationMatrix


def project(points, camera_params, image_params):
    """Convert 3-D points to 2-D by projecting onto images."""
    # rot =
    points_proj = []

    for i, (p, cam, img) in enumerate(zip(points, camera_params, image_params)):
        K = np.array([
            [cam[0],   0, cam[2]],
            [0, cam[1], cam[3]],
            [0,   0,  1]])
        R = eulerAnglesToRotationMatrix(img[0], img[1], img[2])
        t = img[3:6]
        p2d = K@R.T@(p-t)
        p2d /= p2d[2]
        points_proj.append(p2d[:2])
    return np.array(points_proj)


def fun(params, n_cameras, n_images, n_points, camera_indices, image_indices, point_indices, points_2d):
    """Compute residuals.

    `params` contains camera parameters and 3-D coordinates.
    """
    camera_params = params[:n_cameras * 4].reshape((n_cameras, 4))
    image_params = params[n_cameras * 4: n_cameras *
                          4+n_images*6].reshape((n_images, 6))
    # print(image_params)
    points_3d = params[n_cameras*4+n_images*6:].reshape((n_points, 3))
    # print(points_2d[0])
    points_proj = project(
        points_3d[point_indices], camera_params[camera_indices], image_params[image_indices])
    # print(points_proj[0])
    print((points_proj - points_2d).ravel())
    return (points_proj - points_2d).ravel()


def bundle_adjustment_sparsity(n_cameras, n_images, n_points, camera_indices, image_indices, point_indices):
    m = image_indices.size * 2
    n = n_cameras * 4 + n_images * 6 + n_points * 3
    A = lil_matrix((m, n), dtype=int)

    i = np.arange(image_indices.size)

    for s in range(4):
        A[2 * i, camera_indices * 4 + s] = 1
        A[2 * i + 1, camera_indices * 4 + s] = 1

    for s in range(6):
        A[2 * i, n_cameras * 4 + image_indices * 6 + s] = 1
        A[2 * i + 1, n_cameras * 4 + image_indices * 6 + s] = 1

    for s in range(3):
        A[2 * i, n_cameras * 4 + n_images * 6 + point_indices * 3 + s] = 1
        A[2 * i + 1, n_cameras * 4 + n_images * 6 + point_indices * 3 + s] = 1

    return A


def ausgleichung(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""SELECT kid, fx, fy, x0, y0 FROM kameras""")
    cameras = np.array(cur.fetchall())
    # TODO: wahre Werte laden
    cameras = np.array([[1, -3000, -3000, 2000, 1500]])
    camera_params = cameras[:, 1:]
    n_cameras = len(camera_params)

    cur.execute("""SELECT bid, kamera, lrx,lry,lrz,lx,ly,lz FROM bilder""")
    images = np.array(cur.fetchall())
    image_params = images[:, 2:]
    n_images = len(image_params)

    cur.execute("""SELECT pid, lx, ly, lz FROM passpunkte""")
    passpunkte = np.array(cur.fetchall())
    points_3d = passpunkte[:, 1:]
    n_points = len(points_3d)

    cur.execute("""SELECT p.pid, p.bid, bilder.kamera, p.x, 3000-p.y FROM passpunktpos p join bilder on bilder.bid = p.bid join kameras on kameras.kid = bilder.kamera""")  # ORDER BY RANDOM() LIMIT 1000""")
    messungen = np.array(cur.fetchall())
    points_2d = messungen[:, 3:]

    cam_trans = list(cameras[:, 0])
    camera_indices = np.array([cam_trans.index(int(i))
                              for i in list(messungen[:, 2])])
    img_trans = list(images[:, 0])
    image_indices = np.array([img_trans.index(int(i))
                             for i in list(messungen[:, 1])])
    poi_trans = list(passpunkte[:, 0])
    point_indices = np.array([poi_trans.index(int(i))
                             for i in list(messungen[:, 0])])
    print(len(points_2d))

    x0 = np.hstack(
        (camera_params.ravel(), image_params.ravel(), points_3d.ravel()))
    print(len(x0))
    f0 = fun(x0, n_cameras, n_images, n_points, camera_indices,
             image_indices, point_indices, points_2d)
    A = bundle_adjustment_sparsity(
        n_cameras, n_images, n_points, camera_indices, image_indices,  point_indices)

    res = least_squares(fun, x0, jac_sparsity=A, verbose=2, x_scale='jac', ftol=1e-4, method='trf',
                        args=(n_cameras, n_images, n_points, camera_indices, image_indices, point_indices, points_2d))
    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    ausgleichung('./example_data/bildverband2/datenbank.db')
