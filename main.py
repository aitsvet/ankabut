import os
import sys
import json
import sqlite3

from db import DB
from doc import Doc

def main():
    
    dir = sys.argv[1]
    db = DB()
    for filename in os.listdir(dir):
        db.add_doc(Doc(os.path.join(dir, filename)).doc)

    with open(sys.argv[2], 'w') as f:
        json.dump(db.db, f, ensure_ascii=False)

    with sqlite3.connect(sys.argv[3]) as conn:    
        db.store(conn)

if __name__ == '__main__':
    main()
