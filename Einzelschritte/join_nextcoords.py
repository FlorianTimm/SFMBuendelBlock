import cv2
import sqlite3
import numpy as np
from naeherungswerte import reconstruct_one_point
import matplotlib.pyplot as plt


def join_nextcoords(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    cur.execute("""SELECT p.pid, 
        ppa.x, ppa.y, ppb.x, ppb.y, 
        ba.lx, ba.ly, ba.lz, ba.lrx, ba.lry, ba.lrz, ka.fx, ka.fy, ka.x0, ka.y0, 
        bb.lx, bb.ly, bb.lz, bb.lrx, bb.lry, bb.lrz, kb.fx, kb.fy, kb.x0, kb.y0 
        FROM bilder ba 
        JOIN kameras ka on ba.kamera = ka.kid
        JOIN passpunktpos ppa ON ppa.bid = ba.bid
        JOIN passpunkte p ON ppa.pid = p.pid
        JOIN passpunktpos ppb on ppb.pid = p.pid
        JOIN bilder bb ON bb.bid = ppb.bid
        JOIN kameras kb on bb.kamera = kb.kid
        WHERE p.lx is null AND ba.bid != bb.bid AND bb.lx is not null AND ba.lx is not null group by p.pid 
        ORDER BY (1<<(bb.lx - ba.lx) + 1<<(bb.ly - ba.ly) + 1<(bb.lz-ba.lz)) DESC""")

    neue = cur.fetchall()

    pneu = []

    for pid, ppax, ppay, ppbx, ppby, alx, aly, alz, alrx, alry, alrz, afx, afy, ax0, ay0, blx, bly, blz, blrx, blry, blrz, bfx, bfy, bx0, by0 in neue:

        R1, _ = cv2.Rodrigues(np.array([alrx, alry, alrz]))
        P1 = np.c_[R1, [alx, aly, alz]]
        K1 = np.array([[afx, 0, ax0],
                      [0, afy, ay0],
                      [0, 0, 1]])

        R2, _ = cv2.Rodrigues(np.array([blrx, blry, blrz]))
        P2 = np.c_[R2, [blx, bly, blz]]
        K2 = np.array([[bfx, 0, bx0],
                      [0, bfy, by0],
                      [0, 0, 1]])

        p1n = np.dot(np.linalg.inv(K1), np.array([ppax, ppay, 1]))
        p2n = np.dot(np.linalg.inv(K2), np.array([ppbx, ppby, 1]))

        pn = reconstruct_one_point(p1n, p2n, P1, P2)
        pneu.append([pn[0], pn[1], pn[2], pid])

    tripoints3d = np.array(pneu).T
    fig = plt.figure()
    fig.suptitle('3D reconstructed', fontsize=16)
    ax = fig.add_subplot(projection='3d')
    ax.plot(tripoints3d[0], tripoints3d[1], tripoints3d[2], 'r.')
    ax.plot([0], [0], [0], 'g.')
    ax.plot(-P2[0, 3], -P2[1, 3], -P2[2, 3], 'g.')
    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')
    ax.view_init(elev=135, azim=90)
    plt.axis('square')
    ax.set_ylim([-2, 3])
    ax.set_xlim([-2, 3])
    ax.set_zlim([-2, 3])
    plt.show()
    cur.executemany(
        """UPDATE passpunkte SET lx = ?, ly = ?, lz = ? WHERE pid = ?""", pneu)

    print(cur.rowcount)

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    join_nextcoords('./example_data/bildverband2/datenbank.db')
