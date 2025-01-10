import sys

from db import DB
from vis import visualize_authors_keywords

def main(command, src, dst):
    db = DB(src)
    if command == 'scan':
        db.store_json(dst)
    elif command == 'load':
        db.store_sqlite(dst)
    elif command == 'plot':
        visualize_authors_keywords(db, dst)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
