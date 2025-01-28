import re

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 3), None)

def keywords(line):
    return [kw.strip().lower() for kw in re.split(r'[,.;]+', line) if kw]

def table_row(last, line):
    return ' | '.join([l.strip()+' '+n.strip() for l, n in zip(last.split('|'), line.split('|'))]).strip()

def word_count(doc):
    return sum([sum([len(p.split()) for p in s['content']]) for s in doc['sections'] if 'content' in s])

def remove_blank_lines(text):
    return '\n'.join([line for line in text.splitlines() if line.strip()])

def sort_docs(docs):
    return sorted(docs, key=lambda x: (x['year'], x['authors'][0]))

class TreeList():
    
    def __init__(self, text):
        lines = text.strip().split('\n')
        stack = []
        self.tree = []
        for line in lines:
            number_part = re.match(r'^\s*([0-9.]+)\s*', line.strip())
            if not number_part:
                stack = [{'title': line.strip()}]
                self.tree.append(stack[0])
                continue
            levels = number_part.group(1).split('.')
            item = {'title': line.strip()}
            depth = len(levels) + 1
            while len(stack) >= depth:
                stack.pop()
            if stack:
                parent = stack[-1]
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(item)
            else:
                self.tree.append(item)
            stack.append(item)

    def _traverse(self, visitor, tree, path):
        for node in tree:
            if 'children' in node:
                self._traverse(visitor, node['children'], path + [node['title']])
            else:
                visitor(path, node)

    def traverse(self, visitor):
        self._traverse(visitor, self.tree, [])
