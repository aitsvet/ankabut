import os
import sys
import json
import sqlite3

from db import DB
from doc import Doc

def main(command, source, dest):
    if command == 'scan':
        db = DB()
        for filename in os.listdir(source):
            db.add_doc(Doc(os.path.join(source, filename)).doc)
        with open(dest, 'w') as f:
            json.dump(db.db, f, ensure_ascii=False)
    elif command == 'load':
        db = DB(source)
        with sqlite3.connect(dest) as conn:
            db.store(conn)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
