import pathlib
from pyvis.network import Network
import Levenshtein

from parser import author_name

def props(cfg):
    return {'shape': cfg['shape'], 'color': cfg['color'], 'font': {'color': cfg['font']['color']}}

def run(db, cfg, dst: pathlib.Path):
    net = Network(cfg['width'], cfg['height'])
    weight = int(cfg['edge']['weight'])
    threshold = int(cfg['threshold']['keytags'])
    distance = int(cfg['threshold']['levenshtein'])
    t, k = db.db['tags'], db.db['keywords']
    counts = {kt.replace('-', ''): max(t.get(kt, 0), k.get(kt, 0)) for kt in set(t.keys() | k.keys())}
    keytags = sorted(list(set(counts.keys()) - set(cfg['synonyms'].keys())))
    for kt in keytags:
        node, count = kt, counts[kt]
        for kk in keytags:
            if kk == kt:
                break
            if len(kt) > distance * 2 and Levenshtein.distance(kk, kt) <= distance:
                counts[kk] += counts[kt]
                counts[kt] = 0
                node, count = kk, counts[kk]
                break
        if count > threshold:
            label = node.replace(' ', '\n').replace('-', '-\n')
            net.add_node(node, label=label, **props(cfg['keyword']))
    for s1, s2 in cfg['synonyms'].items():
        counts[s2] = max(counts[s1], counts[s2])
        counts[s1] = 0
        if counts[s2] > threshold:
            label = s2.replace(' ', '\n').replace('-', '-\n')
            net.add_node(s2, label=label, **props(cfg['keyword']))
    # [print(k, v) for k, v in sorted(counts.items(), key=lambda x: x[1])]
    for doc in db.db['docs']:
        if 'tags' in doc or 'keywords' in doc:
            doc_keytags = [kt.replace('-', '') for kt in set(doc['tags'] + doc['keywords'])]
            if any(counts[kt] > threshold for kt in doc_keytags):
                net.add_node(doc['path'], label=str(doc['year']), **props(cfg['doc']))
                for author in doc['authors']:
                    net.add_node(author_name(author), **props(cfg['author']))
                    net.add_edge(doc['path'], author_name(author), weight=weight)
                for kt in doc_keytags:
                    if counts[kt] > threshold:
                        net.add_edge(doc['path'], kt, weight=weight)
                    elif kt in cfg['synonyms'] and counts[cfg['synonyms'][kt]] > threshold:
                        net.add_edge(doc['path'], cfg['synonyms'][kt], weight=weight)
                    elif counts[kt] == 0: # synonym
                        for kk in keytags:
                            if counts[kk] > threshold and Levenshtein.distance(kk, kt) <= distance:
                                net.add_edge(doc['path'], kk, weight=weight)
                                break
    net.toggle_physics(True)
    net.show(dst.as_posix(), notebook=False)