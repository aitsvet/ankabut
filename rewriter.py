import pathlib
import jq

import llm
import parser
import tree

class New():

    def __init__(self, db, dst: pathlib.Path, cfg):
        self.dst = dst
        self.client = llm.Client(cfg)
        self.docs = parser.sort_docs(db.db['docs'])
        self.title = cfg['title']
        self.tree = tree.List('', dst)
        gen_cfg = cfg['prompts']['rewrite_paragraph']
        self.limit = int(gen_cfg.get('max_tokens', 8192) * gen_cfg.get('token_factor', 3.0))
        print(f'generation sources list limit: {self.limit}\n')
        self.template = gen_cfg['template']

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.client.chat(prompt, values))

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
        for (num, doc) in enumerate(self.docs):
            author = ', '.join(map(parser.author_name, doc['authors']))
            source += f'{num+1}. {author} ({doc['year']}) {doc['title']}.\n\n'
        return source

    def rewriter(self, path, node):
        if 'children' in node or 'rewrite' in node:
            return
        source = self.build('rewrite', node['title'], 'generate')
        node['rewrite'] = self.chat('rewrite_paragraph', {'source': source, 'paragraph': node['generate']})
        print(node['rewrite'])
        self.tree.save()

    def rewrite(self):
        self.tree.traverse(self.rewriter)
        source = self.build('rewrite')
        values = {'title': self.tree.tree[0]['title'], 'source': source}
        intro = self.chat('write_paragraph', values)
        self.tree.tree[0] = {'rewrite': intro}
        values = {'title': self.tree.tree[-1]['title'], 'source': source}
        outro = self.chat('write_paragraph', values)
        self.tree.tree[-1] = {'rewrite': outro}
        self.tree.save()
        return self.build('rewrite')
