import re

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 3), None)

class DB:

    def __init__(self, path):
        self.db = {'docs': [], 'authors': {}, 'keywords': {}, 'references': []}

    def add_doc(self, doc):
        self.db['docs'].append(doc)
        self.db['references'] += doc['references']
        if 'keywords' in doc:
            for kw in doc['keywords']:
                self.db['keywords'][kw] = self.db['keywords'].get(kw, 1) + 1
        for author in doc['authors']:
            name = author_name(author)
            if name:
                self.db['authors'][name] = self.db['authors'].get(name, []).append(author)

    def migrate(self, conn):
        doc_id = 'doc_id TEXT NOT NULL'
        pk = 'PRIMARY KEY (doc_id, '
        tables = {
            'docs': ['doc_id TEXT PRIMARY KEY', 'title TEXT NOT NULL', 'summary TEXT'],
            'authors': ['author_id TEXT PRIMARY KEY', 'name TEXT'],
            'docs_authors': [doc_id, 'author_id TEXT NOT NULL', pk + 'author_id)'],
            'keywords': [doc_id, 'keyword TEXT NOT NULL', pk + 'keyword)'],
            'references': [doc_id, 'reference_id INTEGER AUTOINCREMENT', 'reference TEXT NOT NULL', pk + 'reference_id)'],
            'sections': [doc_id, 'section_id INTEGER AUTOINCREMENT', 'title TEXT', pk + 'section_id)'],
            'paragraphs': [doc_id, 'section_id INTEGER NOT NULL', 'paragraph_id INTEGER AUTOINCREMENT', 'content TEXT',
                        pk + 'section_id, paragraph_id)', 'FOREIGN KEY (doc_id, section_id) REFERENCES sections(doc_id, section_id)'],
        }
        cursor = conn.cursor()
        for name, fields in tables:
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {name} ( {', '.join(fields)} )')
        conn.commit()

    def store(self, conn):
        self.migrate(conn)
        cursor = conn.cursor()
        for doc in self.db['docs']:
            cursor.execute('INSERT INTO docs (doc_id, title, summary) VALUES (?, ?, ?)',
                        (doc['path'], doc['title'], doc.get('summary', None)))
            doc_id = doc['path']
            for author in doc['authors']:
                name = author_name(author)
                cursor.execute('INSERT INTO authors (author_id, name) VALUES (?, ?) ON CONFLICT DO NOTHING', (author, name))
                cursor.execute('INSERT INTO docs_authors (doc_id, author_id) VALUES (?, ?)', (doc_id, author))
            if 'keywords' in doc:
                for keyword in doc['keywords']:
                    cursor.execute('INSERT INTO keywords (doc_id, keyword) VALUES (?, ?)', (doc_id, keyword))
            for reference in doc['references']:
                cursor.execute('INSERT INTO references (doc_id, reference) VALUES (?, ?)', (doc_id, reference))
            for section in doc['sections']:
                cursor.execute('INSERT INTO sections (doc_id, title) VALUES (?, ?)', (doc_id, section.get('title', None)))
                section_id = cursor.lastrowid
                for content in section['content']:
                    cursor.execute('INSERT INTO paragraphs (doc_id, section_id, content) VALUES (?, ?, ?)', (doc_id, section_id, content))
        conn.commit()