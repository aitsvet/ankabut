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

    def build_source(self, doc, limit, scale):
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
            buffer = self.summarize(scale, buffer)
        return buffer

    def plan(self):
        sources, citations = '', []
        current_plan = self.build_sections(endline='\n')
        print(current_plan)
        start = parser.leading_numbers(self.dst_doc)[0] if 'citations' in self.dst_doc else 0
        total = len(self.embedder.docs)
        sorted_docs = parser.sort_docs(self.embedder.docs)[start:]
        for (n, doc) in enumerate(sorted_docs, start+1):
            authors = ', '.join(map(parser.author_name, doc['authors']))
            limit = self.limit - len(current_plan) - len(sources)
            scale, message = parser.summary_scale(doc, limit)
            buffer = self.build_source(doc, limit, scale)
            last_doc = n == len(sorted_docs)
            if self.onebyone or last_doc or len(buffer) < limit:
                sources += f"# {doc['title']}\n\n{buffer}"
                citations.append(f"{n}. {authors} ({doc['year']}) {doc['title']}")
                print(f"{n} из {total} {doc['year']} {authors} - {doc['title']} - {message}\n")
                if not self.onebyone and not last_doc: # == len(buffer) < limit
                    continue
            if self.onebyone and len(sources) > limit:
                sources = self.summarize(scale, sources)
            next_plan = parser.remove_blank_lines(self.chat('plan', {
                'plan': current_plan,
                'sources': sources
            }))
            # print(next_plan)
            self.sections = parser.sections_from_plan(next_plan)
            self.dst_db.add_doc({
                'title': self.title,
                'sections': self.sections,
                'citations': citations
            })
            self.dst_db.save(self.dst)
            if self.onebyone:
                sources, citations = '', []
            else:
                sources = f"# {doc['title']}\n\n{buffer}"
                citations = [f"{n}. {authors} ({doc['year']}) {doc['title']}"]
            current_plan = self.build_sections(endline='\n')
            print(current_plan)
