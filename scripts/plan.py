import llm
import parser
import database

def summarizer(client, scale, source):
    word_limit = int(len(source) * scale)
    return client.chat('summary', {
        'source': source,
        'min': word_limit - 20 if word_limit > 20 else 20,
        'max': word_limit + 20 if word_limit > 20 else 40,
    }).strip() + '\n\n'

def run(db, cfg, dst):
    dst_db = database.Load(dst)
    onebyone = cfg['onebyone']
    client = llm.Client(cfg)
    title = dst_db.db['docs'][0]['title']
    plan = '\n'.join([s['title'] for s in dst_db.db['docs'][0]['sections']])
    plan_cfg = cfg['prompts']['plan']
    plan_limit = int(plan_cfg.get('max_tokens', 8192) * plan_cfg.get('token_factor', 3.0))
    t = len(db.db['docs'])
    source = ''
    sorted_docs = parser.sort_docs(db.db['docs'])
    for (n, doc) in enumerate(sorted_docs):
        author = parser.author_name(doc['authors'][0])
        words = parser.word_count(doc)
        chars = parser.char_count(doc)
        plan_prompt = cfg['prompts']['plan']['template'].format(title=title, plan=plan, source=source)
        limit = plan_limit - len(plan_prompt)
        scale = (limit / chars) * (words / chars)
        source += '# ' + doc['title'] + '\n\n'
        buffer = ''
        for sec in doc['sections']:
            if 'title' in sec:
                buffer += '## ' + sec['title'] + '\n\n'
            paragraphs = ''
            for par in sec['paragraphs']:
                paragraphs += par['content'] + '\n\n'
            if onebyone and len(paragraphs) > limit:
                paragraphs = summarizer(client, scale, paragraphs)
            buffer += paragraphs
            if onebyone and len(buffer) > limit:
                source += summarizer(client, scale, buffer)
                buffer = ''
        if onebyone or n+1 == len(sorted_docs) or len(buffer) < limit:
            source += buffer
            print(f'{n+1} из {t} {doc['year']} {author} {doc['title']} - {words} слов {chars} симв ' +
                                        f'(лимит {int(chars * scale)} слов {limit} симв)\n')
            if len(buffer) < limit and n+1 != len(sorted_docs):
                continue
        if onebyone and len(source) > limit:
            source = summarizer(client, scale, source)
        plan = client.chat('plan', {
            'title': title,
            'plan': plan,
            'source': source
        })
        plan = parser.strip_thoughts(parser.remove_blank_lines(plan))
        print(plan + '\n')
        source = '' if onebyone else buffer
