import json
import numpy
import faiss
import pathlib

import re
import jq

import llm
import parser
from embedder import Index

class Embedder():

    def __init__(self, db, client: llm.Client, dst: pathlib.Path, cfg):
        self.docs = parser.sort_docs(db.db['docs'])
        self.client = client
        self.title = cfg['title']
        self.plan = '\n'.join(re.sub(r'^(\s*)[0-9.]+ ', r'\1 ', l) for l in cfg['plan'].split('\n'))
        self.window_size = cfg.get('window_size', 2)
        self.max_samples = cfg.get('max_samples', 10)
        gen_cfg = cfg['prompts']['generate']
        self.limit = int(gen_cfg['options'].get('num_ctx', 8192) * gen_cfg.get('token_factor', 3.0))
        values = {'title': self.title, 'plan': self.plan, 'paragraph': '', 'sources': ''}
        self.limit -= len(cfg['prompts']['generate']['template'].format(**values))
        print(f'generation sources list limit: {self.limit}\n')
        self.dst = dst
        ids_file = dst.with_suffix('.ids')
        ems_file = dst.with_suffix('.ems')
        with open(ids_file, 'r') as f:
            self.ids = f.readlines()
        self.ems = faiss.read_index(ems_file.as_posix())

    def generate(self, tree, path, node):
        input = '\n'.join([re.sub(r'^[0-9. ]+', '', p) for p in path + [node['title']]])
        print(input)
        em = self.client.embed(input)
        dists, indices = self.ems.search(numpy.array([em]), k=self.max_samples)
        print(indices[0])
        sources = ''        
        node['sources'] = []
        sources_dist = []
        for dist, idx in zip(dists[0], indices[0]):
            id = self.ids[idx]
            if any(s['i'] == id for s in node['sources']):
                continue
            node['sources'].append({'i': id, 'd': str(dist)})
            doc_id, sec_id, par_id = id.split(':')
            (num, doc) = [(n, d) for (n, d) in enumerate(self.docs) if d['path'] == doc_id][0]
            author = parser.author_name(doc['authors'][0])
            sources += f'Из источника {num+1}. {author} ({doc['year']}) {doc['title']}:\n\n'
            sources_dist.append({'n': num, 't': f'{num+1}. {id.strip()} ({dist:.8f})'})
            content = doc['sections'][int(sec_id)]['content']
            par_id = int(par_id)
            for p in range(par_id - self.window_size, par_id + self.window_size):
                if p >= 0 and p < len(content):
                    sources += content[p] + '\n\n'
            if len(sources) > self.limit:
                break
        print('\n'.join(map(lambda s: s['t'], sorted(sources_dist, key=lambda s: (s['n'], s['t'])))))
        node['generate'] = self.client.chat('generate', {
            'title': self.title,
            'plan': self.plan,
            'paragraph': node['title'],
            'sources': sources
        }) + '\n\n'
        print(node['generate'])
        with open(self.dst, 'w') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)

    def rewrite(self, tree, path, node):
        source = build(self.title, tree, 'rewrite', node['title'], 'generate')
        for (num, doc) in enumerate(self.docs):
            author = ', '.join(map(parser.author_name, doc['authors']))
            source += f'{num+1}. {author} ({doc['year']}) {doc['title']}.\n\n'
        try: start = node['generate'].index('</think>') + 8
        except: start = 0
        node['rewrite'] = self.client.chat('rewrite_paragraph', {
            'source': source,
            'paragraph': node['generate'][start:]
        })
        print(node['rewrite'])
        with open(self.dst, 'w') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)
        
def build(title, tree, head, current, tail):
    field = head
    source = f'# {title}\n\n## 1. Введение\n\n'
    query = '.. | objects | {title: .title?, generate: .generate?, rewrite: .rewrite?} | select(.title != null or .content != null)'
    for line in jq.compile(query).input(tree).all():
        if current == line['title']:
            field = tail
        source += f'## {line['title']}'
        if field in line and line[field]:
            try: start = line[field].index('</think>') + 8
            except: start = 0
            source += line[field][start:]
    source += '## 4. Заключение\n\n## Список использованных источников\n\n'
    return source

def run(db, cfg, dst: pathlib.Path):
    client = llm.Client(cfg)
    embedder = Embedder(db, client, dst, cfg)
    plan = parser.TreeList(cfg['plan'])
    if not dst.exists():
        plan.traverse(embedder.generate)
    else:
        with open(dst, 'r') as f:
            plan.tree = json.load(f)
    plan.traverse(embedder.rewrite)
    source = build(cfg['title'], plan.tree, 'rewrite', None, None)
    plan.tree.insert(0, {'rewrite': client.chat('write_paragraph', {'title': 'Введение', 'source': source})})
    plan.tree.append({'rewrite': client.chat('write_paragraph', {'title': 'Заключение', 'source': source})})
    print(build(cfg['title'], plan.tree, 'rewrite', None, None))
