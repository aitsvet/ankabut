import json
import numpy
import faiss
import pathlib

import re
import jq

import llm
import parse

class Embedder():

    def build_index(self):
        ids, ems = [], []
        for doc in self.docs:
            for (i, sec) in enumerate(doc['sections']):
                for (j, par) in enumerate(sec['content']):
                    lower = par.strip().lower()
                    if not any(lower.startswith(p) for p in ['табл', 'рис', '| ']):
                        ids.append(f'{doc['path']}:{i}:{j}')
                        print(ids[-1] + '\n\n' + par + '\n\n')
                        ems.append(self.client.embed(par))
        arr = numpy.array(ems)
        index = faiss.IndexFlatL2(arr.shape[1])
        index.add(arr)
        return ids, index

    def __init__(self, db, client: llm.Client, dst: pathlib.Path, cfg):
        self.docs = parse.sort_docs(db.db['docs'])
        self.client = client
        self.window_size = cfg.get('window_size', 0)
        self.title = cfg['title']
        self.plan = cfg['plan']
        ids_file = dst.with_suffix('.ids')
        ems_file = dst.with_suffix('.ems')
        if not ids_file.exists() or not ems_file.exists():
            self.ids, self.ems = self.build_index()
            faiss.write_index(self.ems, ems_file.as_posix())
            with open(ids_file, 'w') as f:
                f.writelines([id + "\n" for id in self.ids])
        else:
            with open(ids_file, 'r') as f:
                self.ids = f.readlines()
            self.ems = faiss.read_index(ems_file.as_posix())

    def generate(self, path, leaf):
        input = '\n'.join([re.sub(r'^[0-9. ]+', '', p) for p in path + [leaf['title']]])
        em = self.client.embed(input)
        dists, indices = self.ems.search(numpy.array([em]), k=20)
        sources = ''        
        leaf['sources'] = []
        for d, i in zip(dists[0], indices[0]):
            id = self.ids[i]
            if any(s['i'] == id for s in leaf['sources']):
                continue
            leaf['sources'].append({'i': id, 'd': str(d)})
            doc_id, sec_id, par_id = id.split(':')
            (num, doc) = [(n, d) for (n, d) in enumerate(self.docs) if d['path'] == doc_id][0]
            author = parse.author_name(doc['authors'][0])
            sources += f'Из источника {num}. {author} ({doc['year']}) {doc['title']}:\n\n'
            content = doc['sections'][int(sec_id)]['content']
            par_id = int(par_id)
            for p in range(par_id - self.window_size, par_id + self.window_size):
                if p >= 0 and p < len(content):
                    sources += content[p] + '\n\n'
        leaf['content'] = self.client.chat('generate', {
            'title': self.title,
            'plan': self.plan,
            'paragraph': leaf['title'],
            'sources': sources
        }) + '\n\n'

def run(db, cfg, dst: pathlib.Path):
    if not dst.exists():
        embedder = Embedder(db, llm.Client(cfg), dst, cfg)
        plan = parse.TreeList(cfg['plan'])
        plan.traverse(embedder.generate)
        with open(dst, 'w') as f:
            json.dump(plan.tree, f, indent=2, ensure_ascii=False)
        data = plan.tree
    else:
        with open(dst, 'r') as f:
            data = json.load(f)
    query = '.. | objects | {title: .title?, content: .content?} | select(.title != null or .content != null)'
    for line in jq.compile(query).input(data).all():
        print(line['title'])
        if 'content' in line and line['content']:
            print(line['content'])
