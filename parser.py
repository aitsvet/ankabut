import base64
import re
import gzip
import struct
import yaml
import unicodedata

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 2), None)

def keywords(line):
    return [re.sub(r'\s+', ' ', kw.strip().lower()) for kw in re.split(r'[,.;]+', line) if kw]

def table_row(last, line):
    return ' | '.join([l.strip()+' '+n.strip() for l, n in zip(last.split('|'), line.split('|'))]).strip()

def word_count(doc):
    return sum([sum([len(p['content'].split()) for p in s['paragraphs']]) for s in doc['sections'] if 'paragraphs' in s])

def char_count(doc):
    return sum([sum([len(p['content']) for p in s['paragraphs']]) for s in doc['sections'] if 'paragraphs' in s])

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

def trim_filename(text, sep=' ', max_len=255):
    text = unicodedata.normalize('NFC', text.strip())
    text = re.sub(r'[\\/*?:"<>|\s]+', sep, text).encode()
    if len(text) > max_len:
        text = text[:max_len].rsplit(sep.encode(), 1)[0]
    return text.decode().strip()

def pack_vector(float_list: list[float]) -> str:
    float_bytes = struct.pack(f'{len(float_list)}d', *float_list)
    compressed_bytes = gzip.compress(float_bytes)
    return base64.b64encode(compressed_bytes).decode('utf-8')

def unpack_vector(base64_str: str) -> list[float]:
    compressed_bytes = base64.b64decode(base64_str)
    raw_bytes = gzip.decompress(compressed_bytes)
    return list(struct.unpack(f'{len(raw_bytes)//8}d', raw_bytes))

def leading_numbers(line: str):
    m = re.match(r'^[#\s]*([0-9.]+)\s', line.strip())
    if not m:
        return []
    else:
        return list(map(int, filter(None, m.group(1).split('.'))))
