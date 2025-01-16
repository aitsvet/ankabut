import json

import llm

def join_paragraphs(sections, max_words):
    summaries = []
    for section in sections:
        if not 'content' in section:
            continue
        blocks = []
        block = []
        block_words = 0
        for paragraph in section['content']:
            words = len(paragraph.split())
            if block_words + words > max_words:
                blocks.append(block)
                block = []
                block_words = 0
            block.append(paragraph)
            block_words += words
        if block:
            blocks.append(block)
        for i in range(len(blocks)):
            if i > 0:
                prev_block = blocks[i - 1]
                if prev_block:
                    if prev_block[-1] == blocks[i][0]:
                        blocks[i].insert(0, prev_block[-2])
                    else:
                        blocks[i].insert(0, prev_block[-1])
            if i < len(blocks) - 1:
                next_block = blocks[i + 1]
                if next_block:
                    blocks[i].append(next_block[0])
        summaries.append({'blocks': blocks})
        if 'title' in section:
            summaries[-1]['title'] = section['title']
    return summaries

def run(db, cfg):
    client = llm.Client(cfg)
    keywords = '["' + '", "'.join(db.db['keywords'].keys()) + ']"'
    print(keywords)
    for doc in db.db['docs']:
        sections = doc['sections']
        values = {'input': '', 'keywords': keywords}
        words_in_sections = sum([sum([len(p.split()) for p in s.get('content', [])]) for s in sections])
        if words_in_sections < cfg['max_words']:
            values['description'] = 'приведён исходный текст статьи'
            for section in sections:
                if 'title' in section:
                    values['input'] += '## ' + section['title'] + '\n\n'
                if 'content' in section:
                    values['input'] += '\n\n'.join(section['content'])
        else:
            values['description'] = 'приведены аннотации последовательных абзацев статьи, по одной на строке'
            for section in join_paragraphs(sections, cfg['max_words']):
                for block in section['blocks']:
                    input = ''
                    if 'title' in section:
                        input += '## ' + section['title'] + '\n\n'
                    input += '\n\n'.join(block)
                    values['input'] += '\n' + client.chat('section', {'input': input})
        if not 'llm' in doc:
            doc['llm'] = []
        doc['llm'].append(json.loads(client.chat('paper', values)))
