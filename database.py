import json
import sqlite3
from pathlib import Path

import schema
import parse
import document

class Load:

    def __init__(self, src: Path, cfg):
        self.db = {'docs': [], 'authors': {}, 'keywords': {}, 'citations': []}
        if src.is_dir():
            for file in src.iterdir():
                self.add_doc(document.Load(file, cfg).doc)
        elif src.suffix == '.json':
            with open(src, 'r') as f:
                self.db = json.load(f)
        elif src.suffix == '.sqlite':
            with sqlite3.connect(src) as conn:
                schema.migrate(conn.cursor())
                cursor = conn.cursor()
                cursor.execute('SELECT doc_id, year, title, abstract FROM docs')
                for doc in cursor.fetchall():
                    self.add_doc(schema.load_doc(cursor, doc))

    def add_doc(self, doc):
        self.db['docs'].append(doc)
        self.db['citations'] += doc['citations']
        if 'keywords' in doc:
            for kw in doc['keywords']:
                self.db['keywords'][kw] = self.db['keywords'].get(kw, 0) + 1
        for author in doc['authors']:
            name = parse.author_name(author)
            if name:
                if not name in self.db['authors']:
                    self.db['authors'][name] = []
                self.db['authors'][name].append(author)

    def save(self, dst: Path):
        if dst.suffix == '.json':
            with open(dst, 'w') as f:
                json.dump(self.db, f, ensure_ascii=False)
        elif dst.suffix == '.sqlite':
            with sqlite3.connect(dst) as conn:
                cursor = conn.cursor()
                schema.migrate(cursor)
                for doc in self.db['docs']:
                    schema.store_doc(cursor, doc)
                conn.commit()
