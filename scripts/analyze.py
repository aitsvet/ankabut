import numpy as np
import pathlib

import embedder
from analyze import graph, distmap, closest

def run(db, cfg, dst: pathlib.Path):
    em = embedder.Index(db, cfg, dst)
    n = em.ems.ntotal
    vectors = np.empty((n, em.ems.d), dtype=np.float32)
    for i in range(n):
        vectors[i] = em.ems.reconstruct(i)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    normalized = vectors / norms
    cosine_similarity = np.dot(normalized, normalized.T)
    cosine_distance = 1 - cosine_similarity
    tpl = graph.print(db, cfg['graph'], dst)
    tpl = distmap.print(em, cfg['distmap'], tpl, cosine_distance)
    clt = closest.print(em, cfg['closest'], cosine_distance)
    tpl = tpl.replace('<div id="closest"></div>', clt)
    dst.write_text(tpl)