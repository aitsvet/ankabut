from pathlib import Path
import markdown
import weasyprint

import parser

def run(db, cfg, dst: Path):
    t = len(db.db['docs'])
    output = ''
    for (n, doc) in enumerate(parser.sort_docs(db.db['docs']), 1):
        author = parser.author_name(doc['authors'][0])
        words = parser.word_count(doc)
        chars = parser.char_count(doc)
        output += f'# {n} из {t} - {doc['year']} г. - {author} - {doc['title']} - {words} слов {chars} символов\n\n'
        if 'abstract' in doc:
            output += f'Аннотация. {doc['abstract']}\n\n'
        if 'keywords' in doc:
            output += f'Ключевые слова: {", ".join(doc['keywords'])}\n\n'
        for sec in doc['sections']:
            if 'title' in sec:
                output += '## ' + sec['title'] + '\n\n'
            for par in sec['paragraphs']:
                output += par['content'] + '\n\n'
    if dst.suffix == '.md':
        with open(dst, 'w') as f:
            f.write(output)
    if dst.suffix == '.pdf':
        weasyprint.HTML(string=markdown.markdown(output)).write_pdf(dst.as_posix())
