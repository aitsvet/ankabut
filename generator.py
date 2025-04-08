import pathlib
import re
import jq

import parser
import tree
import embedder

class New():

    def __init__(self, db, dst: pathlib.Path, cfg):
        self.embedder = embedder.Index(db, cfg, pathlib.Path(cfg['index']))
        self.dst = dst
        self.title = cfg['title']
        self.plan = cfg['plan']
        self.tree = tree.List(self.plan, dst)
        gen_cfg = cfg['prompts']['generate']
        self.limit = int(gen_cfg['options'].get('num_ctx', 8192) * gen_cfg.get('token_factor', 3.0))
        print(f'generation sources list limit: {self.limit}\n')
        self.template = gen_cfg['template']

    def chat(self, prompt, values):
        return parser.strip_thoughts(self.embedder.client.chat(prompt, values))

    def build(self, head, current = None, tail = None):
        field = head
        source = f'# {self.title}\n\n## 1. Введение\n\n'
        query = '.. | objects | {title: .title?, generate: .generate?, rewrite: .rewrite?} | select(.title != null or .content != null)'
        for line in jq.compile(query).input(self.tree.tree).all():
            if current == line['title']:
                field = tail
            source += f'## {line['title']}\n\n'
            if field in line and line[field]:
                source += line[field]
        source += '## 4. Заключение\n\n## Список использованных источников\n\n'
        for (num, doc) in enumerate(self.embedder.docs):
            author = ', '.join(map(parser.author_name, doc['authors']))
            source += f'{num+1}. {author} ({doc['year']}) {doc['title']}.\n\n'
        return source

    def generator(self, path, node):
        if 'children' in node or 'generate' in node:
            return
        draft = self.build('generate')
        paragraph = '\n'.join(path + [node['title']])
        values = {'title': self.title, 'plan': self.plan, 'draft': draft, 'paragraph': paragraph, 'sources': ''}
        limit = self.limit - len(self.template.format(**values))
        input = '\n'.join([re.sub(r'^[0-9. ]+', '', p) for p in path + [node['title']]])
        sources = list(self.embedder.search(input, limit))
        sources.reverse()
        values['sources'] = '\n'.join(sources)
        node['generate'] = self.chat('generate', values)
        print(node['generate'])
        self.tree.save()
    
    def generate(self):
        self.tree.traverse(self.generator)
        return self.build('generate')

    def rewriter(self, path, node):
        if 'children' in node or 'rewrite' in node:
            return
        source = self.build('rewrite', node['title'], 'generate')
        node['rewrite'] = parser.strip_thoughts(
            self.embedder.client.chat('rewrite_paragraph', {
                'source': source,
                'paragraph': node['generate']
            }))
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
        return self.build('rewrite')
