import sqlite3
import cv2
import numpy as np


def join_pairs(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()

    #cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsx NUMBER""")
    #cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsy NUMBER""")
    #cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsz NUMBER""")
    #cur.execute("""ALTER TABLE bildpaare ADD COLUMN gpsdist NUMBER""")

    cur.execute(
        """UPDATE bildpaare SET gpsx = d.gpsx, gpsy = d.gpsy, gpsz = d.gpsz FROM (
        SELECT bild1.bid bid1, bild2.bid bid2,
            bild2.x-bild1.x gpsx,
            bild2.y-bild1.y gpsy,
            bild2.z-bild1.z gpsz FROM bilder bild1, bilder bild2) d WHERE bildpaare.bid1 = d.bid1 AND bildpaare.bid2 = d.bid2""")
    cur.execute(
        """UPDATE bildpaare SET gpsdist = sqrt(gpsx*gpsx+gpsy*gpsy+gpsz*gpsz)""")

    db.commit()
    cur.close()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    join_pairs('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
