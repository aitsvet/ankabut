import numpy
import faiss
import pathlib
import re

import llm
import parser

class Index:

    def __init__(self, db, cfg, dst: pathlib.Path):
        self.window_size = cfg['prompts']['embed'].get('window_size', 2)
        self.max_samples = cfg['prompts']['embed'].get('max_samples', 10)
        self.threshold = cfg['prompts']['embed'].get('threshold', 0.0)
        self.client = llm.Client(cfg)
        self.docs = parser.sort_docs(db.db['docs'])
        self.ids, arr = [], []
        for (n, doc) in enumerate(self.docs):
            for (i, sec) in enumerate(doc['sections']):
                for (j, par) in enumerate(sec['content']):
                    self.ids.append(f'{doc['path']}:{i}:{j}')
                    if not dst.exists():
                        print(f'{n+1} из {len(self.docs)} {self.ids[-1]}\n\n{par}\n\n')
                        arr.append(self.client.embed(par))
        if not dst.exists():
            arr = numpy.array(arr)
            self.ems = faiss.IndexFlatL2(arr.shape[1])
            self.ems.add(arr)
            faiss.write_index(self.ems, dst.as_posix())
        else:
            self.ems = faiss.read_index(dst.as_posix())
            if self.ems.ntotal != len(self.ids):
                raise Exception(f'Embedder index has {self.ems.ntotal} != {len(self.ids)} chunks found in document DB')

    def search(self, input, limit = 0):
        em = self.client.embed(input)
        dists, ids = self.ems.search(numpy.array([em]), k=self.max_samples)
        sources_dist = []
        for dist, id in zip(dists[0], ids[0]):
            if self.threshold and dist > self.threshold:
                continue
            id = self.ids[id]
            doc_id, sec_id, par_id = id.split(':')
            (num, doc) = [(n, d) for (n, d) in enumerate(self.docs) if d['path'] == doc_id][0]
            author = parser.author_name(doc['authors'][0])
            c = f'Из источника {num+1}. {author} ({doc['year']}) {doc['title']}:\n\n'
            content = doc['sections'][int(sec_id)]['content']
            par_id = int(par_id)
            for p in range(par_id - self.window_size, par_id + self.window_size + 1):
                if p >= 0 and p < len(content):
                    c += re.sub(r'\[[, 0-9]+\]', '', content[p]) + '\n\n'
            if limit <= 0 or len(c) < limit:
                sources_dist.append({'c': c, 'd': dist})
                limit -= len(c)
        return map(lambda s: s['c'], sorted(sources_dist, key=lambda s: s['d']))