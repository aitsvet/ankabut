from pathlib import Path
import re

import database
import embedder
import parser

class New():

    def __init__(self, db, dst: Path, cfg, prompt_name):
        self.dst = dst
        self.dst_db = database.Load(dst)
        self.title = self.dst_db.db['docs'][-1]['title']
        self.sections = self.dst_db.db['docs'][-1]['sections']
        prev_levels = []
        for (i, sec) in enumerate(self.sections, -1):
            number_part = re.match(r'^([0-9.]+)\s', sec['title'].strip())
            if number_part:
                levels = number_part.group(1).split('.')
                if len(prev_levels) < len(levels):
                    sec['parent'] = i
                elif len(prev_levels) > 0:
                    sec['parent'] = self.sections[i]['parent']
                    if len(prev_levels) > len(levels):
                        sec['parent'] = self.sections[sec['parent']]['parent']
                prev_levels = levels
        self.embedder = embedder.Index(db, cfg, None)
        gen_cfg = cfg['prompts'][prompt_name]
        self.limit = int(gen_cfg.get('max_tokens', 8192) * gen_cfg.get('token_factor', 3.0))
        self.template = gen_cfg['template']

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.embedder.client.chat(prompt, values))

    def build(self, citations = True, endline = '\n\n'):
        source = f'# {self.title}{endline}'
        for sec in self.sections:
            source += f'## {sec['title']}{endline}'
            if 'paragraphs' in sec:
                for par in sec['paragraphs']:
                    source += par['content'] + endline
        if citations:
            for (n, doc) in enumerate(self.embedder.docs, 1):
                author = ', '.join(map(parser.author_name, doc['authors']))
                source += f'{n}. {author} ({doc['year']}) {doc['title']}.{endline}'
        return source
