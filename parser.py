import re
import yaml

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 2), None)

def keywords(line):
    return [re.sub(r'\s+', ' ', kw.strip().lower()) for kw in re.split(r'[,.;]+', line) if kw]

def table_row(last, line):
    return ' | '.join([l.strip()+' '+n.strip() for l, n in zip(last.split('|'), line.split('|'))]).strip()

def word_count(doc):
    return sum([sum([len(p.split()) for p in s['content']]) for s in doc['sections'] if 'content' in s])

def char_count(doc):
    return sum([sum([len(p) for p in s['content']]) for s in doc['sections'] if 'content' in s])

def remove_blank_lines(text):
    return '\n'.join([line for line in text.splitlines() if line.strip()])

def sort_docs(docs):
    return sorted(docs, key=lambda x: (x['year'], x['authors'][0]))

def extend_config(path, cfg):
    try:
        with open(path, 'r') as f:
            for k, v in yaml.safe_load(f).items():
                if k not in cfg:
                    cfg[k] = v
    except: pass

def strip_thoughts(answer):
    start = 0
    if '</think>' in answer:
        start = answer.index('</think>') + 8
    return answer[start:]
