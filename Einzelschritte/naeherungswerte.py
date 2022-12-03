
import math
import sqlite3
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from random import choices


def naeherungswerte(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS bildpaare (
        bid1 INTEGER REFERENCES bilder(bid),
        bid2 INTEGER REFERENCES bilder(bid),
        lx NUMBER, 
        ly NUMBER,
        lz NUMBER,
        lrx NUMBER, 
        lry NUMBER,
        lrz NUMBER
    )""")

    cur.execute("""WITH
    auswahl as (SELECT a.bid abid, b.bid bbid FROM passpunktpos a, passpunktpos b WHERE a.pid = b.pid and a.bid > b.bid group by a.bid, b.bid having count(*) >= 2 order by count(*) desc)
    SELECT abid, bbid, bild1.pfad bild1, bild2.pfad bild2, bild1.kamera kid1, bild2.kamera kid2 FROM auswahl
    LEFT JOIN bilder AS bild1 ON abid = bild1.bid
    LEFT JOIN bilder AS bild2 ON bbid = bild2.bid""")
    bildpaare = cur.fetchall()

    for eintrag in bildpaare:
        bild1, bild2, pfad1, pfad2, kid1, kid2 = eintrag
        pair_pictures(db, bild1, bild2, pfad1, pfad2, kid1, kid2)

    # cur.execute("UPDATE bilder SET lx = 0, ly = 0, lz = 0, lrx = 0, lry = 0, lrz = 0 WHERE bid = ?;",
    #            (passpunkt_liste[0][0],))
    db.commit()
    cur.close()
    db.close()


def pair_pictures(db: sqlite3.Connection, bild1, bild2, pfad1, pfad2, kid1, kid2):
    print(pfad1, pfad2)
    cur = db.cursor()
    cur.execute("""SELECT a.pid pid, a.x ax, a.y ay, b.x bx,  b.y by FROM passpunktpos a, passpunktpos b WHERE a.pid = b.pid and a.bid = ? AND b.bid = ?""", (bild1, bild2)),
    passpunkt_liste = cur.fetchall()

    pts1 = []
    pts2 = []

    for eintrag in passpunkt_liste:
        pid, ax, ay, bx, by = eintrag
        pts1.append([float(ax), float(ay)])
        pts2.append([float(bx), float(by)])
    print(len(pts1))

    pts1 = np.array(pts1)
    pts2 = np.array(pts2)

    F, mask = cv.findFundamentalMat(pts1, pts2, cv.FM_RANSAC)
    pts1 = pts1[mask.ravel() == 1]
    pts2 = pts2[mask.ravel() == 1]
    passpunkt_liste = list(np.array(passpunkt_liste)[mask.ravel() == 1])

    # F, _, _ = findF(pts1, pts2)

    print(len(pts1))

    print(F)
    K1 = get_kameramatrix(cur, kid1)
    K2 = get_kameramatrix(cur, kid2)

    E = K1.T @ F @ K2
    print(E)

    # TODO: nur eine Kameramatrix
    retval, R, t, mask = cv.recoverPose(E, pts1, pts2, K1)

    r_angles = rotationMatrixToEulerAngles(R)
    cur.execute("INSERT INTO bildpaare (bid1, bid2, lx, ly, lz, lrx, lry, lrz) VALUES (?,?,?,?,?,?,?,?);",
                (bild1, bild2, float(t[0]), float(t[1]), float(t[2]), r_angles[0],
                 r_angles[1], r_angles[2]))

    print(r_angles*180/3.41)


def get_kameramatrix(cur: sqlite3.Cursor, kid):
    cur.execute(
        """SELECT c, x0, y0 FROM kameras WHERE kid = ? LIMIT 1""", (kid,))
    c, x0, y0 = cur.fetchone()
    c = 3000
    return np.array([[c, 0, x0],
                     [0, c, y0],
                     [0, 0, 1]])


def calc_points():
    # print("The R_t_0 \n" + str(R_t_0))
    # print("The R_t_1 \n" + str(R_t_1))
    P2 = np.matmul(K, R_t_1)
    pts1 = np.transpose(pts1)
    pts2 = np.transpose(pts2)
    points_3d = cv.triangulatePoints(P1, P2, pts1, pts2)
    points_3d /= points_3d[3]

    for passpunkt, x, y, z in zip(passpunkt_liste, points_3d[0], points_3d[1], points_3d[2]):
        # print(passpunkt)
        db.execute("UPDATE passpunkte SET x=?, y=?, z=? WHERE pid = ?",
                   (x, y, z, passpunkt[2]))

    drawEpi(img1, img2, pts1.T, pts2.T, F)


def rotationMatrixToEulerAngles(R):
    # source: https://learnopencv.com/rotation-matrix-to-euler-angles/
    # assert (isRotationMatrix(R))

    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[2, 1], R[2, 2])
        y = math.atan2(-R[2, 0], sy)
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        y = math.atan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])


def findF(pts1, pts2):
    # source: https://slideplayer.com/slide/3275895/
    # literatur: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=601246
    T = np.array([[2/4000, 0, -1], [0, 2/3000, -1], [0, 0, 1]])
    invT = np.linalg.inv(T)

    pts1T = (T@np.c_[pts1, np.ones(len(pts1))].T).T
    pts2T = (T@np.c_[pts2, np.ones(len(pts2))].T).T

    A_gesamt = []
    for i in range(len(pts1T)):
        ul = pts1T[i][0]
        vl = pts1T[i][1]
        ur = pts2T[i][0]
        vr = pts2T[i][1]
        A_gesamt.append([ur*ul, ur*vl, ur, vr*ul, vr*vl, vr, ul, vl, 1])
    A_gesamt = np.array(A_gesamt)

    inlayers_best = []

    def fund_matrix(indices):
        # source: https://youtu.be/zX5NeY-GTO0?t=1028
        _, _, V = np.linalg.svd(A_gesamt[indices])
        F = V[:, 8].reshape(3, 3).T
        # print(F)
        U, D, V = np.linalg.svd(F)
        # print(U, D, V)
        F = U @ np.diag([D[0], D[1], 0]) @ V.T
        F = T.T@F@T
        F = F * (1/F[2, 2])
        return F

    # RANSAC
    for _ in range(100):
        random = choices(range(len(pts1)), k=8)
        F = fund_matrix(random)

        # source: https://youtu.be/izpYAwJ0Hlw?t=269
        # eigenwert, f = np.linalg.eig(A.T@A)
        # f = f[np.argmin(eigenwert)]
        # F = f.reshape(3, 3).T
        # F = F * (1/F[2, 2])

        inlayers = []
        for i in range(len(pts1)):
            e = np.array([pts1[i][0], pts1[i][1], 1]
                         ).T@F @ np.array([pts2[i][0], pts2[i][1], 1])
            # print(e)
            if e*e < 1000000000:
                inlayers.append(i)
        # print(len(inlayers))
        if len(inlayers_best) < len(inlayers):
            inlayers_best = inlayers
    print(len(inlayers_best))
    pts1 = pts1[inlayers_best]
    pts2 = pts2[inlayers_best]
    F = fund_matrix(inlayers_best)
    return F, pts1, pts2


def safePoints(points_3d):
    with open('test.xyz', 'w') as f:
        for i in range(len(points_3d[0])):
            f.write(str(points_3d[0][i]) + ' ' +
                    str(points_3d[1][i]) + ' ' + str(points_3d[2][i])+'\n')
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(points_3d[0], points_3d[1], points_3d[2])
    plt.show()


def drawEpi(img1, img2, pts1, pts2, F):
    def drawlines(img1, img2, lines, pts1, pts2):
        ''' img1 - image on which we draw the epilines for the points in img2
            lines - corresponding epilines '''
        r, c = img1.shape
        img1 = cv.cvtColor(img1, cv.COLOR_GRAY2BGR)
        img2 = cv.cvtColor(img2, cv.COLOR_GRAY2BGR)
        for r, pt1, pt2 in zip(lines, pts1, pts2):
            print(pt1)
            color = tuple(np.random.randint(0, 255, 3).tolist())
            x0, y0 = map(int, [0, -r[2]/r[1]])
            x1, y1 = map(int, [c, -(r[2]+r[0]*c)/r[1]])
            img1 = cv.line(img1, (x0, y0), (x1, y1), color, 5)

            pt1 = np.int16(pt1)
            pt2 = np.int16(pt2)
            img1 = cv.circle(img1, tuple(pt1), 5, color, -1)
            img2 = cv.circle(img2, tuple(pt2), 5, color, -1)
        return img1, img2

    # Find epilines corresponding to points in right image (second image) and
    # drawing its lines on left image
    lines1 = cv.computeCorrespondEpilines(pts2.reshape(-1, 1, 2), 2, F)
    lines1 = lines1.reshape(-1, 3)
    img5, img6 = drawlines(img1, img2, lines1, pts1, pts2)
    # Find epilines corresponding to points in left image (first image) and
    # drawing its lines on right image
    lines2 = cv.computeCorrespondEpilines(pts1.reshape(-1, 1, 2), 1, F)
    lines2 = lines2.reshape(-1, 3)
    img3, img4 = drawlines(img2, img1, lines2, pts2, pts1)
    plt.subplot(121), plt.imshow(img5)
    plt.subplot(122), plt.imshow(img3)
    plt.show()


if __name__ == "__main__":
    print('Testdaten')
    naeherungswerte('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
