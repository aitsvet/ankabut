import json
import sqlite3

from pathlib import Path
from document import Doc
from parse import author_name
from sqlite import migrate, store_doc, load_doc

class DB:

    def __init__(self, src = None):
        self.db = {'docs': [], 'authors': {}, 'keywords': {}, 'citations': []}
        src = Path(src)
        if src.is_dir():
            for file in src.iterdir():
                self.add_doc(Doc(file).doc)
        elif src.match('*.json'):
            self.from_json(src)
        else:
            self.from_sqlite(src)

    def add_doc(self, doc):
        self.db['docs'].append(doc)
        self.db['citations'] += doc['citations']
        if 'keywords' in doc:
            for kw in doc['keywords']:
                self.db['keywords'][kw] = self.db['keywords'].get(kw, 0) + 1
        for author in doc['authors']:
            name = author_name(author)
            if name:
                if not name in self.db['authors']:
                    self.db['authors'][name] = []
                self.db['authors'][name].append(author)

    def to_json(self, dst):
        with open(dst, 'w') as f:
            json.dump(self.db, f, ensure_ascii=False)

    def from_json(self, src):
        with open(src, 'r') as f:
            self.db = json.load(f)

    def to_sqlite(self, dst):
        with sqlite3.connect(dst) as conn:
            cursor = conn.cursor()
            migrate(cursor)
            for doc in self.db['docs']:
                store_doc(cursor, doc)
            conn.commit()

    def from_sqlite(self, src):
        with sqlite3.connect(src) as conn:
            migrate(conn.cursor())
            cursor = conn.cursor()
            cursor.execute('SELECT doc_id, year, title, summary FROM docs')
            for doc in cursor.fetchall():
                self.add_doc(load_doc(cursor, doc))
