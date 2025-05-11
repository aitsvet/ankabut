from pathlib import Path
import markdown
import weasyprint

import parser

def run(db, cfg, dst: Path):
    t = len(db.db['docs'])
    output = ''
    for (n, doc) in enumerate(parser.sort_docs(db.db['docs']), 1):
        authors = ', '.join(map(parser.author_name, doc.get('authors', [])))
        words = parser.word_count(doc)
        chars = parser.char_count(doc)
        heading = ' - '.join(filter(None, [doc.get('year'), authors, doc.get('title')]))
        output += f'# {n} из {t} - {heading} - {words} слов {chars} символов\n\n'
        if 'abstract' in doc:
            output += f'Аннотация. {doc['abstract']}\n\n'
        if 'keywords' in doc:
            output += f'Ключевые слова: {", ".join(doc['keywords'])}\n\n'
        for sec in doc['sections']:
            if 'title' in sec:
                output += '## ' + sec['title'] + '\n\n'
            if 'paragraphs' in sec:
                for par in sec['paragraphs']:
                    output += par['content'] + '\n\n'
    if dst.suffix == '.md':
        with open(dst, 'w') as f:
            f.write(output)
    if dst.suffix == '.pdf':
        weasyprint.HTML(string=markdown.markdown(output)).write_pdf(dst.as_posix())
