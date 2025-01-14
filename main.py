import sys

import convert
import graph
import database

def main(command, src, dst):
    if command == 'convert':
        convert.from_pdf(src, dst)
    else:
        db = database.DB(src)
        if command == 'scan':
            db.to_json(dst)
        elif command == 'load':
            db.to_sqlite(dst)
        elif command == 'plot':
            graph.authors_keywords(db, dst)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
