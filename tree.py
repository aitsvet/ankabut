import json
import pathlib
import re

class List():
    
    def __init__(self, src, dst):
        self.dst = dst
        if pathlib.Path(self.dst).exists():
            with open(self.dst, 'r') as f:
                self.tree = json.load(f)
            return
        lines = src.strip().split('\n')
        stack = []
        self.tree = []
        print('\n'.join(lines))
        for line in lines:
            number_part = re.match(r'^\s*([0-9.]+)\s*', line.strip())
            levels = number_part.group(1).split('.')
            item = {'title': line.strip()}
            depth = len(levels)
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

    def save(self):
        with open(self.dst, 'w') as f:
            json.dump(self.tree, f, indent=2, ensure_ascii=False)

    def _traverse(self, visitor, tree, path):
        for node in tree:
            visitor(path, node)
            if 'children' in node:
                self._traverse(visitor, node['children'], path + [node['title']])

    def traverse(self, visitor):
        self._traverse(visitor, self.tree[1:-1], [])
