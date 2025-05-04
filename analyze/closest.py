import numpy as np

import embedder

def print(em: embedder.Index, cfg, cosine_distance):
    triu_indices = np.triu_indices(len(cosine_distance), k=1)
    distances_flat = cosine_distance[triu_indices]
    sorted_indices = np.argsort(distances_flat)
    pairs = list(zip(triu_indices[0][sorted_indices], triu_indices[1][sorted_indices]))
    limit = cfg.get('max_samples', 20)
    same_source = cfg.get('same_source', True)
    result = ''
    for n, (i, j) in enumerate(pairs):
        dist = cosine_distance[i, j]
        i = em.get_paragraph(i)
        j = em.get_paragraph(j)
        if not same_source and i['doc_id'] == j['doc_id']:
            continue
        result += f"<div> <p> {n+1}. Cosine Distance: {dist:.4f} </p>"
        result += f"<p> {i['author']} ({i['year']}) - {i['title']} - {i['sec_id']+1} : {i['par_id']+1}</p>"
        result += f"<p> {i['content']} </p>"
        result += f"<p> {j['author']} ({j['year']}) - {j['title']} - {j['sec_id']+1} : {j['par_id']+1}</p>"
        result += f"<p> {j['content']} </p> </div>"
        if limit > 0:
            limit -= 1
        else:
            break
    return f'<div id="closest"> {result} </div>'