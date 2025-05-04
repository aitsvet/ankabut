import pathlib
import re

from generate import builder

class New(builder.New):

    def __init__(self, db, dst: pathlib.Path, cfg):
        super().__init__(db, dst, cfg, 'generate')

    def generator(self, path, node):
        if 'children' in node or 'generate' in node:
            return
        draft = self.build('generate')
        paragraph = '\n'.join(path + [node['title']])
        values = {'title': self.title, 'plan': self.plan, 'draft': draft, 'paragraph': paragraph, 'sources': ''}
        limit = self.limit - len(self.template.format(**values))
        input = '\n'.join([re.sub(r'^[0-9. ]+', '', p) for p in path + [node['title']]])
        sources = list(self.embedder.search(input, limit))
        sources.reverse()
        values['sources'] = '\n'.join(sources)
        node['generate'] = self.chat('generate', values)
        print(node['generate'])
        self.tree.save()
    
    def generate(self):
        self.tree.traverse(self.generator)
        return self.build('generate')
