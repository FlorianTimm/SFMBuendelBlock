from sqlite3 import connect


class transformation:
    def __init__(self, datenbank_pfad: str) -> None:
        self.db = connect(datenbank_pfad)
        self.cursor = self.db.cursor()

    def __del__(self) -> None:
        self.cursor.close()
        self.db.close()
