
import sqlite3
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from random import choices


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

    print(len(pts1))

    pts1 = np.array(pts1)
    pts2 = np.array(pts2)

    A_gesamt = []
    for i in range(len(pts1)):
        ul = pts1[i][0]
        vl = pts1[i][1]
        ur = pts2[i][0]
        vr = pts2[i][1]
        A_gesamt.append([ul*ur, ul*vr, ul, vl*ur, vl*vr, vl, ur, vr, 1])
    A_gesamt = np.array(A_gesamt)

    inlayers_best = []

    def fund_matrix(indices):
        # source: https://youtu.be/zX5NeY-GTO0?t=1028
        _, _, V = np.linalg.svd(A_gesamt[indices])
        f = V[8]
        F = f.reshape(3, 3).T
        F = F * (1/F[2, 2])
        return F

    # RANSAC
    for _ in range(10):
        random = choices(range(len(pts1)), k=8)
        F = fund_matrix(random)

        # source: https://youtu.be/izpYAwJ0Hlw?t=269
        # eigenwert, f = np.linalg.eig(A.T@A)
        # f = f[np.argmin(eigenwert)]
        # F = f.reshape(3, 3).T
        #F = F * (1/F[2, 2])

        inlayers = []
        for i in range(len(pts1)):
            e = np.array([pts1[i][0], pts1[i][1], 1]
                         ).T@F @ np.array([pts2[i][0], pts2[i][1], 1])
            # print(e)
            if e*e < 1:
                inlayers.append(i)
        # print(len(inlayers))
        if len(inlayers_best) < len(inlayers):
            inlayers_best = inlayers
    # print(len(inlayers_best))
    F = fund_matrix(inlayers_best)
    print(F)
    K = np.array([[3000, 0, 2000],
                 [0, 3000, 1500],
                 [0, 0, 1]])
    E = K.T @ F @ K
    print(E)

    img1 = cv.imread(pfad1, 0)
    img2 = cv.imread(pfad2, 0)

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
