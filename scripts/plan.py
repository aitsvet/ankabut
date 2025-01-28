import llm
import parse

def run(db, cfg, dst):
    client = llm.Client(cfg)
    plan = cfg['plan']
    for doc in parse.sort_docs(db.db['docs']):
        author = parse.author_name(doc['authors'][0])
        print(doc['year'], author, doc['title'], parse.word_count(doc), '\n')
        source = '# ' + doc['title'] + '\n\n'
        for sec in doc['sections']:
            if 'title' in sec:
                source += '## ' + sec['title'] + '\n\n'
            for par in sec['content']:
                lower = par.strip().lower()
                if not lower.startswith('табл') and not lower.startswith('| '):
                    source += par + '\n\n'
        plan = client.chat('plan', {
            'title': cfg['title'],
            'plan': plan,
            'source': source
        })
        plan = parse.remove_blank_lines(plan)
        print(plan)
