import pathlib
import re

from generate import builder

class New(builder.New):

    def __init__(self, db, dst: pathlib.Path, cfg):
        super().__init(db, dst, cfg, 'rewrite_paragraph')

    def rewriter(self, path, node):
        if 'children' in node or 'rewrite' in node:
            return
        draft = self.build('rewrite', node['title'], 'generate')
        values = {'draft': draft, 'paragraph': node['generate'], 'sources': ''}
        limit = self.limit - len(self.template.format(**values))
        input = '\n'.join([re.sub(r'^[0-9. ]+', '', p) for p in path + [node['title']]])
        input += '\n' + node['generate']
        sources = list(self.embedder.search(input, limit))
        sources.reverse()
        values['sources'] = '\n'.join(sources)
        node['rewrite'] = self.chat('rewrite_paragraph', values)
        print(node['rewrite'])
        self.tree.save()

    def rewrite(self):
        self.tree.traverse(self.rewriter)
        source = self.build('rewrite')
        values = {'title': self.tree.tree[0]['title'], 'source': source}
        intro = self.chat('write_paragraph', values)
        self.tree.tree[0] = {'rewrite': intro}
        values = {'title': self.tree.tree[-1]['title'], 'source': source}
        outro = self.chat('write_paragraph', values)
        self.tree.tree[-1] = {'rewrite': outro}
        self.tree.save()
        return self.build('rewrite')
