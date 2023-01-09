from metadaten import create_tables as metadaten_create
from aruco import aruco


def create_database(db):
    metadaten_create(db)
    aruco.create_tables(db)
