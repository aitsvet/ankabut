import sys
import json

import convert
import graph
import database
import pathlib
import llm
import parse

def main(src, dst, cfg = None):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    if dst.is_dir():
        convert.from_pdf(src, dst)
    else:
        db = database.Load(src)
        if dst.suffix == '.html':
            graph.authors_keywords(db, dst)
        elif cfg:
            client = llm.Client(cfg)
            for doc in db.db['docs']:
                summaries = []
                for section in parse.summary_ranges(doc['sections'], 100, 300):
                    for block in section['blocks']:
                        text = ''
                        if 'title' in section:
                            text += '## ' + section['title'] + '\n\n'
                        text += '\n\n'.join(block)
                        summaries.append(client.chat('section', text))
                result = json.loads(client.chat('paper', '\n'.join(summaries)))
                doc['llm'] = {
                    'title': result['title'].capitalize(),
                    'keywords': parse.keywords(result['keywords']),
                    'summary': result['summary']
                }
        db.save(dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
