import llm

def run(db, cfg, dst):
    client = llm.Client(cfg)
    d = []
    for doc in db.db['docs']:
        d.append({'sections': []})
        for sec in doc['sections']:
            d[-1]['sections'].append({})
            if 'title' in sec:
                d[-1]['sections'][-1]['title'] = sec['title']
            d[-1]['sections'][-1]['content'] = []
            for par in sec['content']:
                d[-1]['sections'][-1]['content'].append(
                    client.chat('rephrase', {
                        'source': par,
                        'words': len(par.split())
                    }))
    db.db['docs'].append(*d)
    db.save(dst)