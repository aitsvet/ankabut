import traceback

from parser import author_name

def migrate(cursor):
    doc_id = 'doc_id TEXT NOT NULL'
    pk = 'PRIMARY KEY (doc_id, '
    tables = {
        'docs': ['doc_id TEXT PRIMARY KEY', 'year INTEGER NOT NULL', 'title TEXT NOT NULL', 'abstract TEXT'],
        'authors': ['author_id TEXT PRIMARY KEY', 'name TEXT'],
        'docs_authors': [doc_id, 'author_id TEXT NOT NULL', pk + 'author_id)'],
        'keywords': [doc_id, 'keyword TEXT NOT NULL', pk + 'keyword)'],
        'citations': [doc_id, 'citation_id INTEGER NOT NULL', 'citation TEXT NOT NULL', pk + 'citation_id)'],
        'sections': [doc_id, 'section_id INTEGER NOT NULL', 'title TEXT', pk + 'section_id)'],
        'paragraphs': [doc_id, 'section_id INTEGER NOT NULL', 'paragraph_id INTEGER NOT NULL', 'content TEXT',
                    pk + 'section_id, paragraph_id)', 'FOREIGN KEY (doc_id, section_id) REFERENCES sections(doc_id, section_id)'],
    }
    for name, fields in tables.items():
        statement = f'CREATE TABLE IF NOT EXISTS {name} ( {', '.join(fields)} )'
        try:
            cursor.execute(statement)
        except:
            traceback.print_exc()

def store_doc(cursor, doc):
    cursor.execute('INSERT INTO docs (doc_id, year, title, abstract) VALUES (?, ?, ?, ?)',
        (doc['path'], doc['year'], doc['title'], doc.get('abstract', None)))
    doc_id = doc['path']
    for author in doc['authors']:
        name = author_name(author)
        cursor.execute('INSERT INTO authors (author_id, name) VALUES (?, ?) ON CONFLICT DO NOTHING', (author, name))
        cursor.execute('INSERT INTO docs_authors (doc_id, author_id) VALUES (?, ?)', (doc_id, author))
    if 'keywords' in doc:
        for keyword in doc['keywords']:
            cursor.execute('INSERT INTO keywords (doc_id, keyword) VALUES (?, ?)', (doc_id, keyword))
    for citation_id, citation in enumerate(doc['citations']):
        cursor.execute('INSERT INTO citations (doc_id, citation_id, citation) VALUES (?, ?, ?)', (doc_id, citation_id, citation))
    for section_id, section in enumerate(doc['sections']):
        cursor.execute('INSERT INTO sections (doc_id, section_id, title) VALUES (?, ?, ?)', (doc_id, section_id, section.get('title', None)))
        section_id = cursor.lastrowid
        for paragraph_id, content in enumerate(section['content']):
            cursor.execute('INSERT INTO paragraphs (doc_id, section_id, paragraph_id, content) VALUES (?, ?, ?, ?)', (doc_id, section_id, paragraph_id, content))

def load_doc(cursor, doc):
    doc_id, year, title, abstract = doc
    doc = { 'path': doc_id, 'year': year, 'title': title, 'abstract': abstract, 'authors': [], 'keywords': [], 'citations': [], 'sections': [] }
    cursor.execute('SELECT author_id FROM docs_authors WHERE doc_id = ?', (doc_id,))
    for (author_id,) in cursor.fetchall():
        doc['authors'].append(author_id)
    cursor.execute('SELECT keyword FROM keywords WHERE doc_id = ?', (doc_id,))
    for (keyword,) in cursor.fetchall():
        doc['keywords'].append(keyword)
    cursor.execute('SELECT citation FROM citations WHERE doc_id = ? ORDER BY citation_id', (doc_id,))
    for (citation,) in cursor.fetchall():
        doc['citations'].append(citation)
    cursor.execute('SELECT section_id, title FROM sections WHERE doc_id = ? ORDER BY section_id', (doc_id,))
    for section_id, section_title in cursor.fetchall():
        section = { 'title': section_title, 'paragraphs': [] }
        cursor.execute('SELECT content FROM paragraphs WHERE doc_id = ? AND section_id = ? ORDER BY paragraph_id', (doc_id, section_id))
        for (content,) in cursor.fetchall():
            section['paragraphs'].append({'content': content})
        doc['sections'].append(section)
    return doc