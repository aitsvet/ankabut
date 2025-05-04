import pathlib
import jq

import embedder
import parser
import tree

class New():

    def __init__(self, db, dst: pathlib.Path, cfg, prompt_name):
        self.dst = dst
        self.embedder = embedder.Index(db, cfg, None)
        self.title = cfg['title']
        self.tree = tree.List('', dst)
        gen_cfg = cfg['prompts'][prompt_name]
        self.limit = int(gen_cfg.get('max_tokens', 8192) * gen_cfg.get('token_factor', 3.0))
        print(f'generation sources list limit: {self.limit}\n')
        self.template = gen_cfg['template']

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.embedder.client.chat(prompt, values))

    def build(self, head, current = None, tail = None):
        field = head
        source = f'# {self.title}\n\n'
        query = '.. | objects | {title: .title?, generate: .generate?, rewrite: .rewrite?} | select(.title != null or .content != null)'
        for line in jq.compile(query).input(self.tree.tree).all():
            if current == line['title']:
                field = tail
            source += f'## {line['title']}\n\n'
            if field in line and line[field]:
                source += line[field] + '\n\n'
        for (num, doc) in enumerate(self.embedder.docs):
            author = ', '.join(map(parser.author_name, doc['authors']))
            source += f'{num+1}. {author} ({doc['year']}) {doc['title']}.\n\n'
        return source
