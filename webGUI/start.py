import webbrowser
from threading import Timer
from flask import send_from_directory
import os
from flask.json import jsonify
import sqlite3

from flask import Flask
app = Flask(__name__)

PROJEKTPATH = '../projekte/'


@app.route("/")
def hello():
    return "Hello World! <a href='/tool/index.html'>Passpunkt-Tool</a>"


@app.route('/tool/<path:path>')
def send_report(path):
    print(path)
    return send_from_directory('../passpunkt_tool/dist', path)


@app.route('/api/', methods=["GET"])
def get_project():
    return jsonify(os.listdir(PROJEKTPATH))


@app.route('/api/<projekt>', methods=["PUT"])
def create_project(projekt):
    try:
        os.mkdir(PROJEKTPATH + '/' + projekt)
        return 'TRUE'
    except:
        return 'FALSE'


@app.route('/api/<projekt>/images/', methods=["GET", "POST"])
def get_images(projekt):
    if request.method == 'POST':
        f = request.files['the_file']
        f.save(PROJEKTPATH + '/' + projekt + '/images/' + f.filename)
    else:
        db, cursor = open_database(projekt)
        cursor.execute("SELECT 1")
        return jsonify(cursor.fetchmany())


def open_database(projekt):
    path = PROJEKTPATH + '/' + projekt + '/datenbank.db'
    db = sqlite3.connect(path)
    return db, db.cursor()


def open_browser():
    webbrowser.open_new("http://127.0.0.1:2000")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(port=2000)
