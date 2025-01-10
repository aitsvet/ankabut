import json
import sqlite3

from pathlib import Path
from doc import Doc
from fields import author_name
from sql import migrate, store_doc, load_doc

class DB:

    def __init__(self, path = None):
        self.db = {'docs': [], 'authors': {}, 'keywords': {}, 'citations': []}
        path = Path(path)
        if path.is_dir():
            for file in path.iterdir():
                self.add_doc(Doc(file))
        elif path.match('*.json'):
            self.load_json(path)
        else:
            self.load_sqlite(path)

    def add_doc(self, doc):
        self.db['docs'].append(doc)
        self.db['citations'] += doc['citations']
        if 'keywords' in doc:
            for kw in doc['keywords']:
                self.db['keywords'][kw] = self.db['keywords'].get(kw, 1) + 1
        for author in doc['authors']:
            name = author_name(author)
            if name:
                if not name in self.db['authors']:
                    self.db['authors'][name] = []
                self.db['authors'][name].append(author)

    def store_json(self, dst):
        with open(dst, 'w') as f:
            json.dump(self.db, f, ensure_ascii=False)

    def load_json(self, src):
        with open(src, 'r') as f:
            self.db = json.load(f)

    def store_sqlite(self, dst):
        with sqlite3.connect(dst) as conn:
            self.migrate(conn)
            cursor = conn.cursor()
            for doc in self.db['docs']:
                store_doc(cursor, doc)
            conn.commit()

    def load_sqlite(self, src):
        with sqlite3.connect(src) as conn:
            migrate(conn.cursor())
            cursor = conn.cursor()
            cursor.execute('SELECT doc_id, title, summary FROM docs')
            for doc in cursor.fetchall():
                self.add_doc(load_doc(cursor, doc))
