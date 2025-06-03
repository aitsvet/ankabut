from pathlib import Path
import re

import database
import embedder
import parser

class New():

    def __init__(self, db, dst: Path, cfg, prompt_name):
        self.dst = dst
        self.dst_db = database.Load(dst)
        self.dst_doc = self.dst_db.db['docs'][-1]
        self.title = self.dst_doc['title']
        self.sections = self.dst_doc['sections']
        self.embedder = embedder.Index(db, cfg, None)
        gen_cfg = cfg['prompts'][prompt_name]
        self.limit = int(gen_cfg.get('max_tokens', 8192) * gen_cfg.get('token_factor', 3.0))
        self.template = gen_cfg['template']
        self.citations = []
        for (n, doc) in enumerate(self.embedder.docs, 1):
            author = ', '.join(map(parser.author_name, doc['authors']))
            self.citations.append(f'{n}. {author} ({doc["year"]}) {doc["title"]}')

    def build_sections(self, endline = '\n\n'):
        source = f'# {self.title}{endline}'
        for sec in self.sections:
            source += f"## {sec['title']}{endline}"
            if 'paragraphs' in sec:
                for par in sec['paragraphs']:
                    source += par['content'] + endline
        return source

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.embedder.client.chat(prompt, values))
