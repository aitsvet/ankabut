import parser

def run(db, cfg, dst):
    t = len(db.db['docs'])
    for (n, doc) in enumerate(parser.sort_docs(db.db['docs'])):
        author = parser.author_name(doc['authors'][0])
        words = parser.word_count(doc)
        chars = parser.char_count(doc)
        print(f'# {n+1} из {t} {doc['year']} {author} {doc['title']} - {words} слов {chars} симв\n\n')
        if 'abstract' in doc:
            print(f'{doc['abstract']}\n\n')
        if 'keywords' in doc:
            print(f'Keywords: {", ".join(doc['keywords'])}\n\n')
        for sec in doc['sections']:
            if 'title' in sec:
                print('## ' + sec['title'] + '\n\n')
            paragraphs = ''
            for par in sec['content']:
                paragraphs += par + '\n\n'
            print(paragraphs)
