def create_database(db):

    db.execute("""CREATE TABLE IF NOT EXISTS kameras (
            kid INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            fx NUMBER,
            fy NUMBER,
            x0 NUMBER,
            y0 NUMBER,
            pixelx INTEGER,
            pixely INTEGER,
            UNIQUE (model, fx))""")

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

    db.execute("""CREATE TABLE IF NOT EXISTS passpunkte (
                pid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                type TEXT,
                x NUMBER,
                y NUMBER,
                z NUMBER,
                lx NUMBER,
                ly NUMBER,
                lz NUMBER
                )""")

    db.execute("""CREATE TABLE IF NOT EXISTS passpunktpos (
                ppid INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INTEGER REFERENCES passpunkte(pid),
                bid INTEGER REFERENCES bilder(bid),
                x NUMBER,
                y NUMBER,
                UNIQUE (pid, bid))""")
