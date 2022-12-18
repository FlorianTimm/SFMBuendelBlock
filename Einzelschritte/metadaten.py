from glob import glob
import sqlite3
from PIL import Image
from PIL import ExifTags
import utm
from xml.etree import ElementTree as ET
import numpy as np
import math
from random import choices


def metadaten(datenbank, glob_pfad, maxnumber: int = 0):
    print("Metadaten")
    db = sqlite3.connect(datenbank)
    bilder = glob(glob_pfad)
    if not maxnumber == 0:
        bilder = choices(bilder, k=maxnumber)
    db.execute("""CREATE TABLE IF NOT EXISTS bilder (
            bid INTEGER PRIMARY KEY AUTOINCREMENT,
            pfad TEXT UNIQUE,
            kamera INTEGER REFERENCES kameras(kid),
            x NUMBER,
            y NUMBER,
            z NUMBER,
            rx NUMBER,
            ry NUMBER,
            rz NUMBER,
            lx NUMBER,
            ly NUMBER,
            lz NUMBER,
            lrx NUMBER,
            lry NUMBER,
            lrz NUMBER
            )""")

    db.execute("""CREATE TABLE IF NOT EXISTS kameras (
            kid INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            fx NUMBER,
            fy NUMBER,
            x0 NUMBER DEFAULT 0,
            y0 NUMBER DEFAULT 0,
            pixelx INTEGER,
            pixely INTEGER,
            UNIQUE (model, fx))""")

    for bild in bilder:
        print("Bild")
        bildDaten = []
        img = Image.open(bild)
        exif = img._getexif()
        model = ""
        fx, fy, x0, y0, x, y, z, rx, ry, rz, width, height = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        for tag, value in exif.items():
            if 'GPSInfo' == ExifTags.TAGS.get(tag, tag):
                n = float(value[2][0])+float(value[2][1]) / \
                    60.+float(value[2][2])/3600.
                e = float(value[4][0])+float(value[4][1]) / \
                    60.+float(value[4][2])/3600.
                h = float(value[6])
                # x,y,_,_ = utm.from_latlon(n, e, 32)
                # z = h
                x, y, z = to_ecef(n, e, h)
                continue
            if 'Model' == ExifTags.TAGS.get(tag, tag):
                model = str(value)
                continue
            if 'FocalLengthIn35mmFilm' == ExifTags.TAGS.get(tag, tag):
                fx = float(value)
                fy = float(value)
                continue
            if 'ExifImageWidth' == ExifTags.TAGS.get(tag, tag):
                width = int(value)
                x0 = width / 2
                continue
            if 'ExifImageHeight' == ExifTags.TAGS.get(tag, tag):
                height = int(value)
                y0 = height / 2
                continue
            # print(ExifTags.TAGS.get(tag, tag), value)
        with open(bild, "rb") as f:
            s = str(f.read())
            start = s.find('<x:xmpmeta')
            end = s.find('</x:xmpmeta')
            xmp = s[start:end+12].replace("\\n", "\n")
            if xmp:
                tree = ET.XML(xmp)
                # print(xmp)

                rx = float(
                    tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightRollDegree'])/180*math.pi

                ry = float(
                    tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightPitchDegree'])/180*math.pi
                rz = float(
                    tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}FlightYawDegree'])/180*math.pi
        # bildDaten.append(float(tree[0][0].attrib['{http://www.dji.com/drone-dji/1.0/}RelativeAltitude'])/180*math.pi)

        fx = fx / 18. * x0
        fy = fy / 18. * x0

        db.execute(
            "INSERT OR IGNORE INTO kameras (model, fx, fy, x0, y0, pixelx, pixely) VALUES (?,?,?,?,?,?,?)", (model, fx, fy, x0, y0, width, height))
        db.execute(
            "INSERT OR REPLACE INTO bilder (kamera, pfad, x, y, z, rx, ry, rz) VALUES ((SELECT kid FROM kameras WHERE model = ? and fx = ? LIMIT 1), ?,?,?,?,?,?,?)", (model, fx, bild, x, y, z, rx, ry, rz))
    db.commit()
    db.close()


def to_ecef(lat, lon, h):
    lat = math.radians(lat)
    lon = math.radians(lon)
    a = 6378137.0
    b = 6356752.314245
    n = a**2 / math.sqrt(a**2*math.cos(lat)**2 + b**2*math.sin(lat)**2)
    x = (n+h)*math.cos(lat)*math.cos(lon)
    y = (n+h)*math.cos(lat)*math.sin(lon)
    z = (b**2/a**2*n+h)*math.sin(lat)
    return x, y, z


if __name__ == "__main__":
    print('Testdaten')
    metadaten('./example_data/bildverband2/datenbank.db',
              './example_data/bildverband2/*.JPG')
