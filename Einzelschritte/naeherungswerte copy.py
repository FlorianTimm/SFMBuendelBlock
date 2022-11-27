
import sqlite3
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt


def naeherungswerte(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()
    cur.execute("""WITH
    liste as (SELECT a.bid abid, b.bid bbid, a.pid pid, a.x ax, a.y ay, b.x bx,  b.y by FROM passpunktpos a, passpunktpos b WHERE a.pid = b.pid and a.bid > b.bid),
    bester as (SELECT abid, bbid FROM liste group by abid, bbid order by count(*) desc limit 1)
    SELECT liste.*, (select pfad from bilder where liste.abid = bid), (select pfad from bilder where liste.bbid = bid) FROM liste, bester where liste.abid = bester.abid and liste.bbid = bester.bbid""")
    liste = cur.fetchall()

    pts1 = []
    pts2 = []

    for eintrag in liste:
        bild1, bild2, pid, ax, ay, bx, by, pfad1, pfad2 = eintrag
        pts1.append([float(ax), float(ay)])
        pts2.append([float(bx), float(by)])

    print(pfad1, pfad2)

    pts1 = np.float32(pts1)
    pts2 = np.float32(pts2)
    F, mask = cv.findFundamentalMat(pts1, pts2, cv.FM_LMEDS)
    # We select only inlier points
    pts1 = pts1[mask.ravel() == 1]
    pts2 = pts2[mask.ravel() == 1]

    print(F)

    c = 3000

# https://github.com/Ashok93/Structure-From-Motion-SFM-/blob/master/main.py
    K = np.array([[c, 0, 2000], [0, c, 1500], [0, 0, 1]])
    R_t_0 = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
    R_t_1 = np.empty((3, 4))

    E = K.T @ F @ K

    print("The new essential matrix is \n" + str(E))

    retval, R, t, mask = cv.recoverPose(E, pts1, pts2, K)

    print("I+0 \n" + str(R_t_0))

    print("Mullllllllllllll \n" + str(np.matmul(R, R_t_0[:3, :3])))

    R_t_1[:3, :3] = np.matmul(R, R_t_0[:3, :3])
    R_t_1[:3, 3] = R_t_0[:3, 3] + np.matmul(R_t_0[:3, :3], t.ravel())

    print("The R_t_0 \n" + str(R_t_0))
    print("The R_t_1 \n" + str(R_t_1))

    P2 = np.matmul(K, R_t_1)

    #print("The projection matrix 1 \n" + str(P1))
    print("The projection matrix 2 \n" + str(P2))

    pts1 = np.transpose(pts1)
    pts2 = np.transpose(pts2)

    print("Shape pts 1\n" + str(pts1.shape))

    #points_3d = cv.triangulatePoints(P1, P2, pts1, pts2)
    #points_3d /= points_3d[3]

    db.commit()
    cur.close()
    db.close()


def drawlines(img1, img2, lines, pts1, pts2):
    ''' img1 - image on which we draw the epilines for the points in img2
        lines - corresponding epilines '''
    r, c = img1.shape
    img1 = cv.cvtColor(img1, cv.COLOR_GRAY2BGR)
    img2 = cv.cvtColor(img2, cv.COLOR_GRAY2BGR)
    for r, pt1, pt2 in zip(lines, pts1, pts2):
        color = tuple(np.random.randint(0, 255, 3).tolist())
        x0, y0 = map(int, [0, -r[2]/r[1]])
        x1, y1 = map(int, [c, -(r[2]+r[0]*c)/r[1]])
        img1 = cv.line(img1, (x0, y0), (x1, y1), color, 1)
        #img1 = cv.circle(img1, tuple(pt1), 5, color, -1)
        #img2 = cv.circle(img2, tuple(pt2), 5, color, -1)
    return img1, img2


if __name__ == "__main__":
    print('Testdaten')
    naeherungswerte('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
