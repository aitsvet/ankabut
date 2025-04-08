import numpy as np

from parser import author_name
from pyvis.network import Network

def authors_keywords(db, dst):
    net = Network('900px', '100%')
    for author in db.db['authors'].keys():
        net.add_node(author_name(author), shape='ellips', color='green', font={'color': 'white'})
    for keyword, size in db.db['keywords'].items():
        if size > 1:
            label = keyword.replace(' ', '\n').replace('-', '-\n')
            net.add_node(keyword, label=label, shape='box', color='orange', font={'color': 'black'})
    for doc in db.db['docs']:
        if any(db.db['keywords'][kw] > 1 for kw in doc['keywords']):
            net.add_node(doc['path'], label=str(doc['year']), shape='circle', color='lightblue')
            for author in doc['authors']:
                net.add_edge(doc['path'], author_name(author), weight=10)
            for keyword in doc['keywords']:
                if db.db['keywords'][keyword] > 1:
                    net.add_edge(doc['path'], keyword, weight=10)
    net.toggle_physics(True)
    net.show(dst, notebook=False)