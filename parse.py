import re

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 3), None)

def keywords(line):
    return [kw.strip().lower() for kw in re.split(r'[,.]+', line) if kw]

def table(last, line):
    return ' | '.join([l.strip()+' '+n.strip() for l, n in zip(last.split('|'), line.split('|'))]).strip()

def summary_ranges(sections, max_blocks, max_words):
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
        while len(blocks) > max_blocks:
            min1_idx = min2_idx = 0
            min1_len = min2_len = float('inf')
            for i, r in enumerate(blocks):
                r_len = sum(len(s.split()) for s in r)
                if r_len < min1_len:
                    min2_idx, min2_len = min1_idx, min1_len
                    min1_idx, min1_len = i, r_len
                elif r_len < min2_len:
                    min2_idx, min2_len = i, r_len
            blocks[min1_idx].extend(blocks[min2_idx])
            del blocks[min2_idx]
        for i in range(len(blocks)):
            if i > 0:
                prev_block = blocks[i - 1]
                if prev_block:
                    blocks[i].insert(0, prev_block[-1])
                    i += 1
            if i < len(blocks) - 1:
                next_block = blocks[i + 1]
                if next_block:
                    blocks[i].append(next_block[0])
        summaries.append({'blocks': blocks})
        if 'title' in section:
            summaries[-1]['title'] = section['title']
    return summaries