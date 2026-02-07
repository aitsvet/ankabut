import re
import traceback

import parser

class Load:

    def __init__(self, path, cfg):
        self.doc = {'path': path.name, 'ids': [], 'authors': [], 'sections': [{}], 'citations': []}
        self.field = 'paragraphs'
        self.paragraph = []
        self.paragraph_pages = set()
        self.prefix_filter = cfg.get('prefix_filter', [])
        self.min_paragraph = cfg.get('min_paragraph', None)
        self.current_page = None
        number = 1
        try:
            with open(path, 'r') as f:
                line = f.readline().strip()
                while len(line) > 0:
                    self.doc['ids'].append(line)
                    line = f.readline().strip()
                self.doc['journal'] = f.readline().strip()
                self.doc['year'] = self.doc['journal'][:4]
                _, line = f.readline(), f.readline().strip()
                while len(line) > 0:
                    self.doc['authors'].append(line)
                    line = f.readline().strip()
                self.doc['title'] = re.sub(r'^#+', '', f.readline()).strip()
                _, line = f.readline(), f.readline()
                if line.startswith('Tags: '):
                    self.doc['tags'] = parser.keywords(line[6:])
                    _, line = f.readline(), f.readline()
                while line:
                    self.add_line(line.strip())
                    line = f.readline()
                    number += 1
                self.add_paragraph()
        except:
            traceback.print_exc()
            print(f"At {path}:{number} :")

    def add_line(self, line):
        line = line.replace('*', '')
        lower = line.lower()
        
        # Check for page number pattern
        page_match = re.match(r'^\{(\d+)\}---', line)
        if page_match:
            self.current_page = int(page_match.group(1))
            return
        
        if line.startswith('#'):
            if any(t in lower for t in ['список', 'литератур', 'библиог', 'источник', 'примечания', 'reference']) \
                and not any(t in lower for t in ['источников,', 'источники ', 'обзор']):
                self.field = 'citations'
            else:
                if self.doc['sections'][0] == {}:
                    self.doc['sections'] = []
                self.doc['sections'].append({'title': re.sub(r'^#+', '', line).strip()})
        elif lower.startswith('аннотация') or lower.startswith('abstract'):
            self.doc['abstract'] = line[10:].strip()
        elif lower.startswith('ключевые слова') or lower.startswith('keywords') or lower.startswith('key words'):
            self.doc['keywords'] = parser.keywords(line[15:])
        elif len(line) > 0:
            if self.field == 'citations':
                line = re.sub(r'^[0-9]+\.', '', line).strip()
            elif len(self.paragraph) > 0 and re.match(r'^\| +[|а-яa-z]', line.strip()):
                line = parser.table_row(self.paragraph[-1], line)
                self.paragraph = self.paragraph[:-1]
            self.paragraph.append(line)
            if self.current_page is not None:
                self.paragraph_pages.add(self.current_page)
        else:
            self.add_paragraph()
    
    def add_paragraph(self):
        if len(self.paragraph) > 0:
            content = '\n'.join(self.paragraph)
            if self.field == 'paragraphs':
                last = len(self.doc['sections'])-1
                if not 'paragraphs' in self.doc['sections'][last]:
                    self.doc['sections'][last]['paragraphs'] = []
                lower = content.strip().lower()
                paragraphs = self.doc['sections'][last]['paragraphs']
                if not any(lower.startswith(p) for p in self.prefix_filter):
                    if len(paragraphs) > 0 and self.min_paragraph and \
                        len(content.split()) < self.min_paragraph and \
                        len(paragraphs[-1]['content'].split()) < self.min_paragraph:
                        paragraphs[-1]['content'] += '\n' + content
                        # Update pages for merged paragraph
                        if self.paragraph_pages:
                            if 'pages' in paragraphs[-1]:
                                updated_pages = set()
                                if isinstance(paragraphs[-1]['pages'], str):
                                    # Parse existing pages string back to set
                                    updated_pages.update(self._parse_pages_string(paragraphs[-1]['pages']))
                                updated_pages.update(self.paragraph_pages)
                                formatted_pages = self._format_pages(updated_pages)
                                if formatted_pages:
                                    paragraphs[-1]['pages'] = formatted_pages
                            else:
                                formatted_pages = self._format_pages(set(self.paragraph_pages))
                                if formatted_pages:
                                    paragraphs[-1]['pages'] = formatted_pages
                    else:
                        paragraph_data = {'content': content}
                        if self.paragraph_pages:
                            formatted_pages = self._format_pages(set(self.paragraph_pages))
                            if formatted_pages:
                                paragraph_data['pages'] = formatted_pages
                        paragraphs.append(paragraph_data)
            else:
                self.doc[self.field].append(content)
            self.paragraph = []
            self.paragraph_pages = set()
    
    def _format_pages(self, pages):
        if not pages:
            return None
        sorted_pages = sorted(pages)
        if len(sorted_pages) == 1:
            return str(sorted_pages[0])
        else:
            return f"{sorted_pages[0]}-{sorted_pages[-1]}"
    
    def _parse_pages_string(self, pages_str):
        pages = set()
        if '-' in pages_str:
            start, end = map(int, pages_str.split('-'))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(pages_str))
        return pages