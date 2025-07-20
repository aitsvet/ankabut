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
            self.citations.append(f"{n}. {author} ({doc["year"]}) {doc["title"]}")

    def build_section(self, sec, endline = '\n\n', with_title = True, with_parents = False):
        source = ''
        if with_title:
            if 'title' in sec:
                source += f"## {sec['title']}{endline}"
            if with_parents:
                parent = sec['parent']
                while parent > 0:
                    source = f"## {self.sections[parent]['title']}\n\n{source}"
                    parent = self.sections[parent]['parent']
        if 'paragraphs' in sec:
            for par in sec['paragraphs']:
                if 'content' in par:
                    source += par['content'] + endline
        return source

    def build_sections(self, endline = '\n\n', current = None):
        source = f"# {self.title}{endline}"
        for sec in self.sections:
            if sec == current:
                break
            source += self.build_section(sec, endline)
        return source

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.embedder.client.chat(prompt, values))
