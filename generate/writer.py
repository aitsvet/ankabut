import pathlib
import copy

import parser
from generate import builder

class New(builder.New):

    def __init__(self, db, dst: pathlib.Path, cfg):
        super().__init__(db, dst, cfg, 'write')
        self.sections = parser.copy_and_link_parents(self.sections)
        self.plan = self.build_sections()
    
    def write(self):
        self.dst_db.add_doc(copy.deepcopy(self.dst_doc))
        new_doc = self.dst_db.db['docs'][-1]
        for sec in new_doc['sections']:
            if not 'paragraphs' in sec:
                continue
            input = self.build_section(sec, with_parents=True)
            print(input)
            values = {
                'plan': self.plan,
                'section': sec['title'],
                'draft': self.build_sections(),
                'sources': ''
            }
            limit = self.limit - len(self.template.format(**values))
            values['sources'] = '\n'.join(reversed(self.embedder.search(input, limit)))
            print(values['sources'])
            output = self.chat('write', values)
            print(output)
            sec['paragraphs'] = [{ 'content': l } for l in map(str.strip, output.splitlines()) if l]
            self.dst_db.save(self.dst)
