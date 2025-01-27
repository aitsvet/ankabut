import llm

def run(db, cfg, dst):
    client = llm.Client(cfg)
    for d in db.db['paragraphs']:
        d['words'] = len(d[-1].split())
        d.append(client.chat('rephrase', d))
    db.save(dst)