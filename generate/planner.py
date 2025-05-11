from pathlib import Path
import re

import parser
from generate import builder

class New(builder.New):

    def __init__(self, db, dst: Path, cfg):
        super().__init__(db, dst, cfg, 'plan')
        self.onebyone = cfg['onebyone']

    def summarize(self, scale, source):
        word_limit = int(len(source) * scale)
        return self.chat('summary', {
            'source': source,
            'min': word_limit - 20 if word_limit > 20 else 20,
            'max': word_limit + 20 if word_limit > 20 else 40,
        }).strip() + '\n\n'

    def plan(self):
        citations = []
        sources = ''
        current = self.build(citations=False, endline='\n')
        print(current)
        start = 0
        if 'citations' in self.dst_db.db['docs'][-1]:
            start = parser.leading_numbers(self.dst_db.db['docs'][-1]['citations'][-1])[0]
        total = len(self.embedder.docs)
        sorted_docs = parser.sort_docs(self.embedder.docs[start:])
        for (n, doc) in enumerate(sorted_docs, start+1):
            authors = ', '.join(map(parser.author_name, doc['authors']))
            words = parser.word_count(doc)
            chars = parser.char_count(doc)
            limit = self.limit - len(current) - len(sources)
            scale = (limit / chars) * (words / chars)
            word_limit = limit * words // chars
            sources += '# ' + doc['title'] + '\n\n'
            buffer = ''
            for sec in doc['sections']:
                if 'title' in sec:
                    buffer += '## ' + sec['title'] + '\n\n'
                paragraphs = ''
                for par in sec['paragraphs']:
                    paragraphs += par['content'] + '\n\n'
                if self.onebyone and len(paragraphs) > limit:
                    paragraphs = self.summarize(scale, paragraphs)
                buffer += paragraphs
                if self.onebyone and len(buffer) > limit:
                    sources += self.summarize(scale, buffer)
                    buffer = ''
            if self.onebyone or n == len(sorted_docs) or len(buffer) < limit:
                sources += buffer
                citations.append(f'{n}. {authors} ({doc['year']}) {doc['title']}')
                print(f'{n} из {total} {doc['year']} {authors} - {doc['title']} - ' +
                      f'{words} слов {chars} символов (лимит {word_limit} слов {limit} символов)\n')
                if len(buffer) < limit and n != len(sorted_docs):
                    continue
            if self.onebyone and len(sources) > limit:
                sources = self.summarize(scale, sources)
            next = parser.remove_blank_lines(self.chat('plan', {
                'title': self.title,
                'plan': current,
                'sources': sources
            }))
            print(next)
            self.sections = []
            for l in next.splitlines():
                if parser.leading_numbers(l):
                    self.sections.append({'title': re.sub(r'^[#\s]+', '', l)})
                elif len(self.sections) > 0:
                    if 'paragraphs' not in self.sections[-1]:
                        self.sections[-1]['paragraphs'] = [{'content': l}]
                    else:
                        self.sections[-1]['paragraphs'].append({'content': l})
            self.dst_db.add_doc({
                'title': self.title,
                'sections': self.sections,
                'citations': citations
            })
            self.dst_db.save(self.dst)
            citations = [] if self.onebyone else [f'{n}. {authors} ({doc['year']}) {doc['title']}']
            sources = '' if self.onebyone else buffer
            current = self.build(citations=False, endline='\n')
            print(current)
