import numpy
import faiss
import pathlib
import re

import llm
import parser
import database

class Index:

    def __init__(self, db: database.Load, cfg, dst: pathlib.Path):
        embed_cfg = cfg.get('prompts', {}).get('embed', {})
        self.window_size = embed_cfg.get('window_size', 2)
        self.max_samples = embed_cfg.get('max_samples', 10)
        self.threshold = embed_cfg.get('threshold', 0.0)
        self.model = embed_cfg.get('model', 'bge-m3')
        self.client = llm.Client(cfg)
        self.docs = parser.sort_docs(db.db['docs'])
        self.ids, arr = [], []
        need_save = False
        for (n, doc) in enumerate(self.docs):
            for (i, sec) in enumerate(doc['sections']):
                for (j, par) in enumerate(sec['paragraphs']):
                    self.ids.append(f"{doc['path']}:{i}:{j}")
                    if self.model in par.get('embedding', {}):
                        arr.append(parser.unpack_vector(par['embedding'][self.model]))
                    else:
                        need_save = True
                        print(f"{n+1} из {len(self.docs)} {self.ids[-1]}\n\n{par["content"]}\n\n")
                        vector = self.client.embed(par['content'])
                        arr.append(vector)
                        if 'embedding' in par:
                            par['embedding'][self.model] = parser.pack_vector(vector)
                        else:
                            par['embedding'] = {self.model: parser.pack_vector(vector)}
        arr = numpy.array(arr)
        self.ems = faiss.IndexFlatL2(arr.shape[1])
        self.ems.add(arr)
        if need_save and dst and dst.suffix == '.json':
           db.save(dst)

    def search(self, input, limit = 0):
        em = self.client.embed(input)
        dists, ids = self.ems.search(numpy.array([em]), k=self.max_samples)
        sources_set = {}
        for dist, id in zip(dists[0], ids[0]):
            if self.threshold and dist > self.threshold:
                continue
            id = self.ids[id]
            doc_id, sec_id, par_id = id.split(':')
            (num, doc) = [(n, d) for (n, d) in enumerate(self.docs) if d['path'] == doc_id][0]
            sec_id, par_id = int(sec_id), int(par_id)
            paragraphs = doc['sections'][sec_id]['paragraphs']
            if not num in sources_set:
                sources_set[num] = {}
            if not sec_id in sources_set[num]:
                sources_set[num][sec_id] = {}
            for p in range(par_id - self.window_size, par_id + self.window_size + 1):
                if p >= 0 and p < len(paragraphs):
                    sources_set[num][sec_id][p] = dist
        sources_dist = []
        for (num, secs) in sorted(sources_set.items()):
            doc = self.docs[num]
            min_dist = 0.0
            c = ''
            for (sec_id, pars) in sorted(secs.items()):
                paragraphs = doc['sections'][sec_id]['paragraphs']
                for (par_id, dist) in sorted(pars.items()):
                    if dist < min_dist:
                        min_dist = dist
                    c += re.sub(r'\[[, 0-9]+\]', '', paragraphs[par_id]['content']) + '\n\n'
            author = parser.author_name(doc['authors'][0])
            c = f"Из источника {num+1}. {author} ({doc['year']}) {doc['title']}:\n\n" + c
            sources_dist.append({'c': c, 'd': min_dist})
        result = []
        for s in sorted(sources_dist, key=lambda s: s['d']):
            if limit <= 0 or len(c) < limit:
                result.append(s['c'])
                limit -= len(c)
        return result
    
    def get_paragraph(self, idx):
        doc_id, sec_id, par_id = self.ids[idx].split(':')
        doc = next(d for d in self.docs if d['path'] == doc_id)
        return {
            'doc_id': doc_id,
            'sec_id': int(sec_id),
            'par_id': int(par_id),
            'year': doc['year'],
            'title': doc['title'],
            'author': parser.author_name(doc['authors'][0]),
            'content': doc['sections'][int(sec_id)]['paragraphs'][int(par_id)]['content']
        }
