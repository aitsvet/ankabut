import re
import traceback

from fields import keywords

class Doc:

    def __init__(self, path):
        self.doc = {'path': path.name, 'authors': [], 'sections': [{}], 'citations': []}
        self.field = 'authors'
        self.paragraph = []
        number = 1
        try:
            with open(path, 'r') as f:
                line = f.readline()
                self.doc['year'] = line.strip()
                line = f.readline()
                while line:
                    self.add_line(line.strip())
                    line = f.readline()
                    number += 1
                self.add_paragraph()
        except:
            traceback.print_exc()
            print(f'At {path}:{number} :')

    def add_line(self, line):
        if line.startswith('# '):
            self.field = 'content'
            self.doc['title'] = line[2:].strip().capitalize()
        elif line.startswith('## '):
            l = line.lower()
            if any(t in l for t in ['список', 'литератур', 'источ']) and not 'обзор' in l:
                self.field = 'citations'
            else:
                if self.doc['sections'][0] == {}:
                    self.doc['sections'] = []
                self.doc['sections'].append({'title': line[3:].strip()})
        elif line.startswith('Аннотация'):
            self.doc['summary'] = line[10:].strip()
        elif line.startswith('Ключевые слова'):
            self.doc['keywords'] = keywords(line[15:])
        elif len(line) > 0:
            if self.field == 'citations':
                line = re.sub(r'^[0-9]+\.', '', line).strip()
            self.paragraph.append(line)
        else:
            self.add_paragraph()
    
    def add_paragraph(self):
        if len(self.paragraph) > 0:
            content = '\n'.join(self.paragraph)
            if self.field == 'content':
                last = len(self.doc['sections'])-1
                if not 'content' in self.doc['sections'][last]:
                    self.doc['sections'][last]['content'] = []
                self.doc['sections'][last]['content'].append(content)
            else:
                self.doc[self.field].append(content)
            self.paragraph = []