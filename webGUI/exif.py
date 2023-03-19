from sqlite3 import connect
from os import mkdir
from os.path import exists
from PIL import Image
from PIL.ExifTags import TAGS
from pyproj import Transformer


class exif:
    def __init__(self, path: str, datenbank_pfad: str) -> None:
        self.db = connect(datenbank_pfad)
        self.cursor = self.db.cursor()
        self.path = path

    def write_exif(self) -> None:
        self.cursor.execute(
            "SELECT pfad, x,y,z,rx,ry,rz FROM bilder WHERE x is NOT NULL")
        bilder = self.cursor.fetchall()
        exif_path = self.path + '/exif'

        if not exists(exif_path):
            mkdir(exif_path)
        print(bilder)

        transformer = Transformer.from_crs(
            {"proj": 'geocent', "ellps": 'WGS84', "datum": 'WGS84'},
            {"proj": 'latlong', "ellps": 'WGS84', "datum": 'WGS84'}
        )

        for bild in bilder:
            (pfad, x, y, z, rx, ry, rz) = bild
            img = Image.open(pfad)
            exif = img.getexif()
            gpsid = list(TAGS.keys())[list(TAGS.values()).index("GPSInfo")]
            gps = exif.get_ifd(gpsid)
            print(gps)

            lon, lat, h = transformer.transform(x, y, z, radians=False)

            ns = 'N'
            if lat < 0:
                ns = 'S'
                lat = -lat

            ew = 'E'
            if lon < 0:
                ew = 'W'
                lon = -lon

            exif.update([(gpsid, {0: b'\x02\x02\x00\x00',
                         1: ns,
                         2: (lat//1, lat % 1*60//1, lat % (1/60)*3600
                             ),
                         3: ew,
                         4: (lon//1, lon % 1*60//1, lon % (1/60)*3600
                             ),
                         5: b'\x00',
                         6: h*1000//1/1000})])
            neuerpfad = exif_path + '/' + pfad.split('/')[-1]
            img.save(neuerpfad, exif=exif)

            print("Schreibe ", pfad, ' nach ', neuerpfad)

    def __del__(self) -> None:
        self.cursor.close()
        self.db.close()
