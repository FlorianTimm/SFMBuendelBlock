from webbrowser import open_new_tab
from flask import Flask, request, send_from_directory, send_file, Response
from os import mkdir, listdir
from os.path import exists
from flask.json import jsonify
from create_database import create_database
from sqlite3 import connect, Connection

from metadaten import load_metadata
from aruco import aruco
from find_sift import find_sift
from match_sift import match_sift
from naeherungswerte import naeherungswerte
from join_nextcoords import join_nextcoords
from join_nextpictures import join_nextpictures
from bundle_adjustment import bundle_adjustment
from exif import exif
from transformation import transformation
from typing import Any, Dict
from werkzeug import Response as WerkzeugResponse

app = Flask(__name__)

PROJEKTPATH = './projekte/'


@app.route("/")
def hello() -> str:
    return "Hello World! <a href='/tool/index.html'>Passpunkt-Tool</a>"


@app.route('/tool/<path:path>')
def send_report(path: str) -> Response:
    print(path)
    return send_from_directory('../passpunkt_tool/dist', path)


@app.route('/api/', methods=["GET"])
def get_project() -> Response:
    return jsonify(listdir(PROJEKTPATH))


@app.route('/api/<projekt>', methods=["PUT"])
def create_project(projekt: str) -> str:
    try:
        mkdir(PROJEKTPATH + '/' + projekt)
        db = open_database(projekt)
        create_database(db)
        return 'TRUE'
    except:
        return 'FALSE'


@app.route('/api/<projekt>/images/', methods=["GET", "POST"])
def get_images(projekt: str) -> Response | str:
    path = PROJEKTPATH + projekt + '/images/'
    if not exists(path):
        mkdir(path)
    if request.method == 'POST':
        f = request.files['file']
        if (f.filename is None or path is None):
            return "FALSE"
        f.save(path + f.filename)
        db = open_database(projekt)
        load_metadata(db, path + f.filename)
        db.commit()
        db.close()
        return "TRUE"
    else:
        db = open_database(projekt)
        cursor = db.cursor()
        cursor.execute(
            "SELECT bid, kamera, lx, ly, lz, lrx, lry, lrz, pixelx, pixely FROM bilder b left join kameras k on k.kid = b.kamera")
        data = [{'bid': b[0],
                 'kamera': b[1],
                 'url':f"/api/{projekt}/images/{b[0]}/file",
                 'x':b[2], 'y':b[3], 'z': b[4],
                 'rx':b[5], 'ry':b[6], 'rz': b[7],
                 'width':b[8], 'height':b[9]}
                for b in cursor.fetchall()]
        db.close()
        return jsonify(data)


@app.route('/api/<projekt>/passpunkte/', methods=["GET", "POST"])
def get_passpunkte(projekt: str) -> str | Response:
    if request.method == 'POST':
        db = open_database(projekt)
        data = request.json
        print(data)
        # TODO: speichern
        db.commit()
        db.close()
        return "TRUE"
    else:
        db = open_database(projekt)
        cursor = db.cursor()
        cursor.execute("SELECT pid, name, type, lx, ly, lz FROM passpunkte")
        data = [{'pid': b[0], 'name': b[1], 'type': b[2], 'x':b[3], 'y':b[4], 'z': b[5]}
                for b in cursor.fetchall()]
        db.close()
        return jsonify(data)


@app.route('/api/<projekt>/passpunkte/<passpunkt>/<image>', methods=["DELETE", "PUT"])
def delete_modify_passpunkte(projekt: str, passpunkt: str, image: str) -> str | Response:
    db = open_database(projekt)
    if request.method == 'DELETE':
        db.execute(
            "DELETE FROM passpunktpos WHERE bid = ? and pid = ?", (image, passpunkt))
        db.commit()
        db.close()
        return "TRUE"
    else:
        daten: Dict[str, Any] | None = request.json
        if daten is None:
            return "FALSE"
        cur = db.cursor()
        if daten['passpunkt'] == -1:
            cur.execute(
                "INSERT INTO passpunkte (name, type) VALUES (?,'manual') RETURNING pid", (daten['name'],))
            daten['passpunkt'] = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO passpunktpos (pid, bid, x, y) VALUES (?,?,?,?) RETURNING ppid", (daten['passpunkt'], daten['image'], daten['x'], daten['y']))
        ppid = cur.fetchone()[0]
        cur.execute(
            "SELECT name, p.pid, bid, pp.x, pp.y FROM passpunktpos pp left join passpunkte p on p.pid = pp.pid WHERE ppid = ?", (ppid,))
        b = cur.fetchone()
        data = {'passpunkt': b[1], 'name': b[0],
                'image': b[2], 'x': b[3], 'y': b[4]}
        cur.close()
        db.commit()
        db.close()
        return jsonify(data)


@app.route('/api/<projekt>/passpunkte/<passpunkt>/position', methods=["GET", "POST"])
def get_passpunkt_bilder(projekt: str, passpunkt: str) -> str | Response:
    db = open_database(projekt)
    if request.method == 'POST':
        data = request.json
        print(data)
        # TODO: speichern
        db.commit()
        db.close()
        return "TRUE"
    else:
        cursor = db.cursor()
        cursor.execute(
            "SELECT name, p.pid, bid, pp.x, pp.y FROM passpunktpos pp left join passpunkte p on p.pid = pp.pid WHERE p.pid = ?", (passpunkt,))
        data = [{'passpunkt': b[1], 'name': b[0], 'image': b[2], 'x': b[3], 'y': b[4]}
                for b in cursor.fetchall()]
        db.close()
        return jsonify(data)


@app.route('/api/<projekt>/image/<image>/passpunkte', methods=["GET"])
def get_bilder_passpunkte(projekt: str, image: str) -> str | Response:
    db = open_database(projekt)
    cursor = db.cursor()
    cursor.execute(
        "SELECT name, p.pid, bid, pp.x, pp.y FROM passpunktpos pp left join passpunkte p on p.pid = pp.pid WHERE bid = ?", (image,))
    data = [{'passpunkt': b[1], 'name': b[0], 'image': b[2], 'x': b[3], 'y': b[4]}
            for b in cursor.fetchall()]
    db.close()
    return jsonify(data)


@app.route('/api/<projekt>/images/<nr>/file')
def show_images(projekt: str, nr: str) -> WerkzeugResponse | Any:
    db = open_database(projekt)
    cursor = db.cursor()
    cursor.execute("SELECT pfad FROM bilder where bid = ?", (nr,))
    pfad = cursor.fetchone()[0]
    print(pfad)
    db.close()
    return send_file('.' + pfad)


@app.route('/api/<projekt>/find_aruco')
def find_aruco(projekt: str) -> str:
    db = open_database(projekt)
    ar = aruco(db)
    ar.find_all_aruco()
    db.close()
    return 'TRUE'


@app.route('/api/<projekt>/find_sift')
def find_sift_all(projekt: str) -> str:
    sift = find_sift(database_path(projekt))
    sift.find_sift_in_all()
    return 'TRUE'


@app.route('/api/<projekt>/match_sift')
def match_sift_all(projekt: str) -> str:
    sift = match_sift(database_path(projekt))
    sift.match_sift()
    return 'TRUE'


@app.route('/api/<projekt>/next_image')
def web_join_nextpictures(projekt: str) -> str:
    join_nextpictures(database_path(projekt))
    return 'TRUE'


@app.route('/api/<projekt>/next_coordinates')
def web_join_nextcoords(projekt: str) -> str:
    join_nextcoords(database_path(projekt))
    return 'TRUE'


@app.route('/api/<projekt>/start_pair')
def start_pair(projekt: str) -> str:
    naeherungswerte(database_path(projekt))
    return 'TRUE'


@app.route('/api/<projekt>/bundle_block')
def bundle_block(projekt: str) -> str:
    bundle_adjustment(database_path(projekt))
    return 'TRUE'


@app.route('/api/<projekt>/exif_download')
def exif_download(projekt: str) -> str:
    transformation(database_path(projekt))
    e = exif(PROJEKTPATH + projekt, database_path(projekt))
    e.write_exif()
    return 'TRUE'


def database_path(projekt: str) -> str:
    return PROJEKTPATH + projekt + '/datenbank.db'


def open_database(projekt: str) -> Connection:
    path = database_path(projekt)
    return connect(path)


def open_browser() -> None:
    open_new_tab("http://127.0.0.1:2000")


if __name__ == "__main__":
    # Timer(1, open_browser).start()
    app.run(port=2000)  # , threaded=False)
