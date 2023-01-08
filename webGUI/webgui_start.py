from webbrowser import open_new_tab
from threading import Timer
from flask import Flask, request, send_from_directory, send_file
from os import mkdir, listdir
from os.path import exists
from flask.json import jsonify
from create_database import create_database
import sqlite3

from metadaten import load_metadata

app = Flask(__name__)

PROJEKTPATH = './projekte/'


@app.route("/")
def hello():
    return "Hello World! <a href='/tool/index.html'>Passpunkt-Tool</a>"


@app.route('/tool/<path:path>')
def send_report(path):
    print(path)
    return send_from_directory('../passpunkt_tool/dist', path)


@app.route('/api/', methods=["GET"])
def get_project():
    return jsonify(listdir(PROJEKTPATH))


@app.route('/api/<projekt>', methods=["PUT"])
def create_project(projekt):
    try:
        mkdir(PROJEKTPATH + '/' + projekt)
        return 'TRUE'
    except:
        return 'FALSE'


@app.route('/api/<projekt>/images/', methods=["GET", "POST"])
def get_images(projekt):
    path = PROJEKTPATH + projekt + '/images/'
    if not exists(path):
        mkdir(path)
    if request.method == 'POST':
        f = request.files['file']
        f.save(path + f.filename)
        db = open_database(projekt)
        load_metadata(db, path + f.filename)

        db.commit()
        return "TRUE"
    else:
        db = open_database(projekt)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM bilder")
        return jsonify(cursor.fetchall())


@app.route('/api/<projekt>/images/<nr>/file')
def show_images(projekt, nr):
    db = open_database(projekt)
    cursor = db.cursor()
    cursor.execute("SELECT pfad FROM bilder where bid = ?", (nr,))
    pfad = cursor.fetchone()[0]
    print(pfad)
    return send_file('.' + pfad)


database_connections = {}


def open_database(projekt):
    if not projekt in database_connections:
        path = PROJEKTPATH + projekt + '/datenbank.db'
        database_connections[projekt] = sqlite3.connect(path)
        #database_connections[projekt].row_factory = sqlite3.Row
        create_database(database_connections[projekt])
    return database_connections[projekt]


def open_browser():
    open_new_tab("http://127.0.0.1:2000")


if __name__ == "__main__":
    #Timer(1, open_browser).start()
    app.run(port=2000, threaded=False)
