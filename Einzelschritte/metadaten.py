from glob import glob
import sqlite3
from PIL import Image
from PIL import ExifTags
import utm
from xml.etree import ElementTree as ET
import numpy as np
import math


def metadaten(datenbank, glob_pfad):
    print("Metadaten")
    db = sqlite3.connect(datenbank)
    bilder = glob(glob_pfad)
    db.execute("""CREATE TABLE IF NOT EXISTS bilder (
            bid INTEGER PRIMARY KEY AUTOINCREMENT,
            pfad TEXT UNIQUE,
            kamera INTEGER REFERENCES kameras(kid),
            x NUMBER,
            y NUMBER,
            z NUMBER,
            rx NUMBER,
            ry NUMBER,
            rz NUMBER
            )""")

    db.execute("""CREATE TABLE IF NOT EXISTS kameras (
            kid INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            c NUMBER,
            x0 NUMBER DEFAULT 0,
            y0 NUMBER DEFAULT 0,
            pixelx INTEGER,
            pixely INTEGER,
            UNIQUE (model, c))""")

    for bild in bilder:
        print("Bild")
        bildDaten = []
        img = Image.open(bild)
        exif = img._getexif()
        model = ""
        c, x, y, z, rx, ry, rz, width, height = 0, 0, 0, 0, 0, 0, 0, 0, 0
        for tag, value in exif.items():
            if 'GPSInfo' == ExifTags.TAGS.get(tag, tag):
                n = float(value[2][0])+float(value[2][1]) / \
                    60.+float(value[2][2])/3600.
                e = float(value[4][0])+float(value[4][1]) / \
                    60.+float(value[4][2])/3600.
                z = float(value[6])
                u = utm.from_latlon(n, e, 32)
                x = float(u[0])
                y = float(u[1])
                continue
            if 'Model' == ExifTags.TAGS.get(tag, tag):
                model = str(value)
                continue
            if 'FocalLength' == ExifTags.TAGS.get(tag, tag):
                c = float(value)
                continue
            if 'ExifImageWidth' == ExifTags.TAGS.get(tag, tag):
                width = int(value)
                continue
            if 'ExifImageHeight' == ExifTags.TAGS.get(tag, tag):
                height = int(value)
                continue
            #print(ExifTags.TAGS.get(tag, tag), value)
        with open(bild, "rb") as f:
            s = str(f.read())
            start = s.find('<x:xmpmeta')
            end = s.find('</x:xmpmeta')
            xmp = s[start:end+12].replace("\\n", "\n")
            tree = ET.XML(xmp)
            # print(xmp)

            rx = float(
                tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightRollDegree'])/180*math.pi

            ry = float(
                tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightPitchDegree'])/180*math.pi
            rz = float(
                tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightYawDegree'])/180*math.pi
        # bildDaten.append(float(tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}RelativeAltitude'])/180*math.pi)

        db.execute(
            "INSERT OR IGNORE INTO kameras (model, c, pixelx, pixely) VALUES (?,?,?,?)", (model, c, width, height))
        db.execute(
            "INSERT OR REPLACE INTO bilder (kamera, pfad, x, y, z, rx, ry, rz) VALUES ((SELECT kid FROM kameras WHERE model = ? and c = ? LIMIT 1), ?,?,?,?,?,?,?)", (model, c, bild, x, y, z, rx, ry, rz))
    db.commit()
    db.close()


if __name__ == "__main__":
    print('Testdaten')
    metadaten('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db',
              './Entwicklung/eigenerAnsatz/bildverband2/*.JPG')
