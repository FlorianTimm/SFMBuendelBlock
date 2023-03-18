
import cv2
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from random import choices
from typing import List, Any
from numpy.typing import NDArray

# functions derived from https://github.com/alyssaq/3Dreconstruction
"""
Copyright © 2022 Alyssa Quek

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files(the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and / or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def naeherungswerte(datenbank: str, show_figures: bool = False) -> None:
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute(
        """UPDATE bilder SET lx = NULL, ly = NULL, lz = NULL, lrx = NULL, lry = NULL, lrz = NULL""")
    cur.execute(
        """UPDATE passpunkte SET lx = NULL, ly = NULL, lz = NULL""")

    cur.execute("""WITH
    liste as (SELECT a.bid abid, b.bid bbid, a.pid pid, a.x ax, a.y ay, b.x bx, b.y by, type FROM passpunktpos a, passpunktpos b, passpunkte p WHERE a.pid = b.pid and a.bid > b.bid and a.pid = p.pid),
    bester as (SELECT abid, bbid FROM liste group by abid, bbid order by sum( CASE WHEN type = 'manual' THEN 3 WHEN type = 'aruco' THEN 2 WHEN type = 'SIFT' THEN 1 END) desc limit 1)
    SELECT liste.* FROM liste, bester  where liste.abid = bester.abid and liste.bbid = bester.bbid""")
    liste: List[List[Any]] = cur.fetchall()

    pts1 = []
    pts2 = []
    pids_array: List[int] = []
    weights = []
    bild1: int = -1
    bild2: int = -1

    for eintrag in liste:
        bild1, bild2, pid, ax, ay, bx, by, typ = eintrag
        # print(eintrag)
        pids_array.append(pid)
        pts1.append([float(ax), float(ay)])
        pts2.append([float(bx), float(by)])

        if (typ == "SIFT"):
            weights.append(1)
        elif (typ == "aruco"):
            weights.append(2)
        else:
            weights.append(3)

    if (bild2 == -1 or bild1 == -1):
        return

    pids = np.array(pids_array, dtype=np.int32)

    cur.execute("UPDATE bilder SET lx = 0, ly = 0, lz = 0, lrx = 0, lry = 0, lrz = 0 WHERE bid = ?;",
                (bild1,))

    K1 = get_kameramatrix(cur, bild1)
    K2 = get_kameramatrix(cur, bild2)

    points1 = cart2hom(np.array(pts1).T)
    points2 = cart2hom(np.array(pts2).T)

    # Calculate essential matrix with 2d points.
    # Result will be up to a scale
    # First, normalize points
    # Hartley p257
    points1n = np.dot(np.linalg.inv(K1), points1)
    points2n = np.dot(np.linalg.inv(K2), points2)
    # cv2.undistortPoints(pts1, intrinsic, None)[:,0,:].T

    print(len(points1n.T))

    maxcount = 0
    maxauswahl: NDArray[Any] | None = None

    for i in range(1000):
        auswahl = choices(range(len(weights)), weights, k=8)

        E = compute_essential_normalized(
            points1n[:, auswahl], points2n[:, auswahl])

        mask = np.array([abs(points2n.T[i].T@E@points1n.T[i]) < 1
                        for i in range(len(points2n.T))])

        count = len(points2n.T[mask])
        if count > maxcount:
            maxcount = count
            maxauswahl = mask

    points1n = points1n.T[maxauswahl].T
    points2n = points2n.T[maxauswahl].T
    pids = pids[maxauswahl]

    E = compute_essential_normalized(points1n, points2n)

    print('Computed essential matrix:', (-E / E[0][1]))

    P1 = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])

    _, R, t, mask = cv2.recoverPose(
        E, points1n[:2].T, points2n[:2].T, np.eye(3))

    R = np.linalg.inv(R)
    t = -R@t

    mask = mask.ravel()
    pids = pids.T[mask == 255].T
    points1n = points1n.T[mask == 255].T
    points2n = points2n.T[mask == 255].T

    rod, _ = cv2.Rodrigues(R)

    cur.execute("UPDATE bilder SET lx = ?, ly = ?, lz = ?, lrx = ?, lry = ?, lrz = ? WHERE bid = ?;",
                (float(t[0]), float(t[1]), float(t[2]), float(rod[0]), float(rod[1]), float(rod[2]), int(bild2)))

    P2 = np.c_[R, t]
    print(P2)

    print(len(points1n.T))

    tripoints3d = reconstruct_points(points1n, points2n, P1, P2)
    # tripoints3d = structure.linear_triangulation(points1n, points2n, P1, P2)

    if (show_figures):
        fig = plt.figure()
        fig.suptitle('3D reconstructed', fontsize=16)
        ax = fig.add_subplot(projection='3d')
        ax.plot(tripoints3d[0], tripoints3d[1], tripoints3d[2], 'r.')
        ax.plot([0], [0], [0], 'g.')
        ax.plot(-P2[0, 3], -P2[1, 3], -P2[2, 3], 'g.')
        ax.set_xlabel('x axis')
        ax.set_ylabel('y axis')
        ax.set_zlabel('z axis')  # type: ignore
        ax.view_init(elev=135, azim=90)  # type: ignore
        plt.axis('square')
        ax.set_ylim(-2, 3)
        ax.set_xlim(-2, 3)
        ax.set_zlim(-2, 3)  # type: ignore
        plt.show()

    datenzip = zip(tripoints3d[0], tripoints3d[1],
                   tripoints3d[2], np.array(pids, dtype=np.int32))
    daten = [[d[0], d[1], d[2], int(d[3])] for d in datenzip]
    cur.executemany(
        "UPDATE passpunkte SET lx = ?, ly = ?, lz = ? WHERE pid = ?", daten)
    print(cur.rowcount)

    cur.close()
    db.commit()
    db.close()


def get_kameramatrix(cur: sqlite3.Cursor, bid: int) -> NDArray[np.float32]:
    cur.execute(
        """SELECT fx, fy, x0, y0 FROM kameras WHERE kid = (SELECT kamera FROM bilder WHERE bid=?) LIMIT 1""", (bid,))
    fx, fy, x0, y0 = cur.fetchone()

    return np.array([[fx, 0, x0],
                     [0, fy, y0],
                     [0, 0, 1]])


def cart2hom(arr: NDArray[np.float32]) -> NDArray[np.float32]:
    """ Convert catesian to homogenous points by appending a row of 1s
    :param arr: array of shape (num_dimension x num_points)
    :returns: array of shape ((num_dimension+1) x num_points)
    """
    if arr.ndim == 1:
        return np.hstack([arr, 1])
    return np.asarray(np.vstack([arr, np.ones(arr.shape[1])]))


def scale_and_translate_points(points: NDArray[np.float32]) -> tuple[Any, NDArray[Any]]:
    """ Scale and translate image points so that centroid of the points
        are at the origin and avg distance to the origin is equal to sqrt(2).
        Hartley p109
    :param points: array of homogenous point (3 x n)
    :returns: array of same input shape and its normalization matrix
    """
    x = points[0]
    y = points[1]
    center = points.mean(axis=1)  # mean of each row
    cx = x - center[0]  # center the points
    cy = y - center[1]
    dist = np.sqrt(np.power(cx, 2) + np.power(cy, 2))
    scale = np.sqrt(2) / dist.mean()
    norm3d = np.array([
        [scale, 0, -scale * center[0]],
        [0, scale, -scale * center[1]],
        [0, 0, 1]
    ])

    return np.dot(norm3d, points), norm3d


def correspondence_matrix(p1: NDArray[np.float32], p2: NDArray[np.float32]) -> NDArray[np.float64]:
    """Each row in the A matrix below is constructed as
        [x'*x, x'*y, x', y'*x, y'*y, y', x, y, 1]
        Hartley p279"""
    p1x, p1y = p1[:2]
    p2x, p2y = p2[:2]

    return np.array([
        p1x * p2x, p1x * p2y, p1x,
        p1y * p2x, p1y * p2y, p1y,
        p2x, p2y, np.ones(len(p1x))
    ]).T


def compute_essential_normalized(p1: NDArray[np.float32], p2: NDArray[np.float32]) -> NDArray[np.float64]:
    """ Computes the fundamental or essential matrix from corresponding points
        using the normalized 8 point algorithm.
        Hartley p294
    :input p1, p2: corresponding points with shape 3 x n
    :returns: fundamental or essential matrix with shape 3 x 3
    """
    n = p1.shape[1]
    if p2.shape[1] != n:
        raise ValueError('Number of points do not match.')

    # preprocess image coordinates
    # Hartley p282
    p1n, T1 = scale_and_translate_points(p1)
    p2n, T2 = scale_and_translate_points(p2)

    # compute F or E with the coordinates
    # Harley p280
    A = correspondence_matrix(p1n, p2n)
    # compute linear least square solution
    U, S, V = np.linalg.svd(A)
    F: NDArray[np.float64] = V[-1].reshape(3, 3)

    # constrain F. Make rank 2 by zeroing out last singular value
    # Hartley p. 259
    U, S, V = np.linalg.svd(F)
    # S[-1] = 0 # Fundamental Hartley p.281
    S = np.array([1, 1, 0])  # Force rank 2 and equal eigenvalues
    F = U @ np.diag(S) @ V

    # reverse preprocessing of coordinates
    # We know that P1' E P2 = 0
    # Hartley p282
    F = T1.T@F@T2

    np.divide(F, F[2, 2], F)
    return F


def reconstruct_points(p1: NDArray[np.float32], p2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    num_points = p1.shape[1]
    res = np.ones((4, num_points))

    for i in range(num_points):
        res[:, i] = reconstruct_one_point(p1[:, i], p2[:, i], m1, m2)

    return res


def skew(x: NDArray[np.float32]) -> NDArray[np.float64]:
    """ Create a skew symmetric matrix *A* from a 3d vector *x*.
        Property: np.cross(A, v) == np.dot(x, v)
    :param x: 3d vector
    :returns: 3 x 3 skew symmetric matrix from *x*
    """
    return np.array([
        [0, -x[2], x[1]],
        [x[2], 0, -x[0]],
        [-x[1], x[0], 0]
    ], dtype=np.float64)


def reconstruct_one_point(pt1: NDArray[np.float32], pt2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    """
        pt1 and m1 * X are parallel and cross product = 0
        pt1 x m1 * X  =  pt2 x m2 * X  =  0
    """
    A = np.vstack([
        np.dot(skew(pt1), m1),
        np.dot(skew(pt2), m2)
    ])
    U, S, V = np.linalg.svd(A)
    P = np.ravel(V[-1, :4])

    np.divide(P, P[3])
    return P


def linear_triangulation(p1: NDArray[np.float32], p2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    """
    Linear triangulation (Hartley ch 12.2 pg 312) to find the 3D point X
    where p1 = m1 * X and p2 = m2 * X. Solve AX = 0.
    :param p1, p2: 2D points in homo. or catesian coordinates. Shape (3 x n)
    :param m1, m2: Camera matrices associated with p1 and p2. Shape (3 x 4)
    :returns: 4 x n homogenous 3d triangulated points
    """
    num_points = p1.shape[1]
    res = np.ones((4, num_points))

    for i in range(num_points):
        A = np.asarray([
            (p1[0, i] * m1[2, :] - m1[0, :]),
            (p1[1, i] * m1[2, :] - m1[1, :]),
            (p2[0, i] * m2[2, :] - m2[0, :]),
            (p2[1, i] * m2[2, :] - m2[1, :])
        ])

        _, _, V = np.linalg.svd(A)
        X = V[-1, :4]
        res[:, i] = X / X[3]

    return res


if __name__ == "__main__":
    print('Testdaten')
    # naeherungswerte('./example_data/bildverband2/datenbank.db')
    naeherungswerte('./example_data/heilgarten.db')
