import re

class TreeList():
    
    def __init__(self, text):
        lines = text.strip().split('\n')
        stack = []
        self.tree = []
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

    def _traverse(self, visitor, tree, path):
        for node in tree:
            visitor(self.tree, path, node)
            if 'children' in node:
                self._traverse(visitor, node['children'], path + [node['title']])

    def traverse(self, visitor):
        self._traverse(visitor, self.tree, [])
