import sqlite3
import json
import csv


def ausgleichung(datenbank):
    db = sqlite3.connect(datenbank)
    cur = db.cursor()
    rec = json.load(
        open('./Entwicklung/OpenSfM/data/halle/reconstruction.json'))[0]
    cameras: dict[str, dict] = rec['cameras']
    shots: dict[str, dict] = rec['shots']
    points: dict[str, dict] = rec['points']


if __name__ == "__main__":
    print('Testdaten')
    ausgleichung('./Entwicklung/eigenerAnsatz/Einzelschritte/datenbank.db')
