import re
import traceback

import parse

class Load:

    def __init__(self, path, cfg):
        self.doc = {'path': path.name, 'authors': [], 'sections': [{}], 'citations': []}
        self.field = 'authors'
        self.paragraph = []
        self.prefix_filter = cfg.get('prefix_filter', [])
        self.min_paragraph = cfg.get('min_paragraph', None)
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
        line = line.replace('*', '')
        lower = line.lower()
        if line.startswith('# '):
            self.field = 'content'
            self.doc['title'] = line[2:].strip().capitalize()
        elif line.startswith('##'):
            if any(t in lower for t in ['список', 'литератур', 'источ', 'reference']) and not 'обзор' in lower:
                self.field = 'citations'
            else:
                if self.doc['sections'][0] == {}:
                    self.doc['sections'] = []
                self.doc['sections'].append({'title': re.sub(r'^#+', '', line).strip()})
        elif lower.startswith('аннотация') or lower.startswith('abstract'):
            self.doc['abstract'] = line[10:].strip()
        elif lower.startswith('ключевые слова') or lower.startswith('keywords'):
            self.doc['keywords'] = parse.keywords(line[15:])
        elif len(line) > 0:
            if self.field == 'citations':
                line = re.sub(r'^[0-9]+\.', '', line).strip()
            elif len(self.paragraph) > 0 and re.match(r'^\| +[|а-яa-z]', line.strip()):
                line = parse.table_row(self.paragraph[-1], line)
                self.paragraph = self.paragraph[:-1]
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
                lower = content.strip().lower()
                paragraphs = self.doc['sections'][last]['content']
                if not any(lower.startswith(p) for p in self.prefix_filter):
                    if len(paragraphs) > 0 and self.min_paragraph and \
                        len(content.split()) < self.min_paragraph and \
                        len(paragraphs[-1].split()) < self.min_paragraph:
                        paragraphs[-1] += '\n' + content
                    else:
                        paragraphs.append(content)
            else:
                self.doc[self.field].append(content)
            self.paragraph = []