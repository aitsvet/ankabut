import llm
import parse

def summarize(client, scale, source):
    word_limit = int(len(source) * scale)
    return client.chat('summary', {
        'source': source,
        'min': word_limit - 20 if word_limit > 20 else 20,
        'max': word_limit + 20 if word_limit > 20 else 40,
    }).strip() + '\n\n'

def run(db, cfg, dst):
    client = llm.Client(cfg)
    title = cfg['title']   
    plan = cfg['plan']
    plan_cfg = cfg['prompts']['plan']
    plan_limit = int(plan_cfg['options'].get('num_ctx', 8192) * plan_cfg.get('token_factor', 3.0))
    t = len(db.db['docs'])
    for (n, doc) in enumerate(parse.sort_docs(db.db['docs'])):
        author = parse.author_name(doc['authors'][0])
        words = parse.word_count(doc)
        chars = parse.char_count(doc)
        plan_prompt = cfg['prompts']['plan']['template'].format(title=title, plan=plan, source='')
        limit = plan_limit - len(plan_prompt)
        scale = (limit / chars) * (words / chars)
        print(f'{n+1} из {t} {doc['year']} {author} {doc['title']} - {words} слов {chars} симв ' +
                                               f'(лимит {int(chars * scale)} слов {limit} симв)\n')
        source = '# ' + doc['title'] + '\n\n'
        buffer = ''
        for sec in doc['sections']:
            if 'title' in sec:
                buffer += '## ' + sec['title'] + '\n\n'
            paragraphs = ''
            for par in sec['content']:
                paragraphs += par + '\n\n'
            if len(paragraphs) > limit:
                paragraphs = summarize(client, scale, paragraphs)
            buffer += paragraphs
            if len(buffer) > limit:
                source += summarize(client, scale, buffer)
                buffer = ''
        source += buffer
        if len(source) > limit:
            source = summarize(client, scale, source)
        plan = client.chat('plan', {
            'title': cfg['title'],
            'plan': plan,
            'source': source
        })
        plan = parse.remove_blank_lines(plan)
        print(plan + '\n')
