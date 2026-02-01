from pathlib import Path

import re
import xml.etree.ElementTree as ET

import pdf
import parser

attrib_prefix = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'

def attrib(elem, name, default = None):
    return elem.attrib.get(attrib_prefix + name, default)

class Convert:

    def __init__(self, src: Path, dst: Path):
        with open(src, 'r') as f:
            self.root = ET.fromstring(f.read())
        with open(src, 'r') as f:
            start = ET.iterparse(f, events=['start-ns'])
            self.nss = {key: value for _, (key, value) in start}
        self.reader = pdf.Reader()
        self.journals = self.all('bib:Journal')
        self.attachments = self.all('z:Attachment')
        for item in self.all('bib:Book') + self.all('bib:Article') + self.all('rdf:Description'):
            self.load_item(item, src, dst)

    def all(self, elem):
        return self.root.findall(elem, self.nss)

    def text(self, parent, path, default = None):
        elem = parent.findtext(path, default, self.nss)
        return elem.strip() if elem != default else default

    def load_item(self, item, src: Path, dst: Path):
        link = item.find('link:link', self.nss)
        if link is None:
            return
        link = attrib(link, 'resource')
        year = self.text(item, 'dc:date')
        authors = item.findall('bib:authors/rdf:Seq/rdf:li/foaf:Person', self.nss)
        firstAuthor = self.text(authors[0], 'foaf:surname')
        title = self.text(item, 'dc:title')
        dstname = parser.trim_filename(f"{year} {firstAuthor} {title}")
        output = dst.joinpath(Path(dstname).with_suffix('.md').name)
        if output.exists():
            return
        if 'dcterms' in self.nss:
            partOf = item.find('dcterms:isPartOf', self.nss)
            journal = partOf.find('bib:Journal', self.nss)
            if journal is None:
                partOf = attrib(partOf, 'resource')
                journal = [j for j in self.journals if attrib(j, 'about') == partOf][0]
            ids = [attrib(item, 'about'), self.text(journal, 'dc:identifier')]
            volume = f'Т.{v}' if 'prism' in self.nss and (v := self.text(journal, 'prism:volume')) else ''
            number = f'№{n}' if 'prism' in self.nss and (n := self.text(journal, 'prism:number')) else ''
            pages = f'С.{p}' if (p := self.text(item, 'bib:pages'))  else ''
            journal = self.text(journal, 'dc:title')
            citation = [year, journal, volume, number, pages]
        else:
            ids = []
            citation = []
        tags = [self.text(tag, 'rdf:value') for tag in item.findall('dc:subject/z:AutomaticTag', self.nss)]
        attachment = [a.find('rdf:resource', self.nss) for a in self.attachments if attrib(a, 'about') == link][0]
        source_path = src.parent.joinpath(attrib(attachment, 'resource')).as_posix()
        source = self.reader.md_from(source_path)
        with open(output, 'w+') as f:
            self.save_item(ids, citation, authors, title, tags, source, f)
        print(f"Written {output}")

    def save_item(self, ids, citation, authors, title, tags, source, f):
        sourcelines = []
        lowerlines = []
        for l in source.splitlines():
            l = l
            if not any(c in l for c in ['=', '/']):
                l = l.replace('**', '').replace('©', '')
                l = re.sub(r'^\*+', '', l)
                l = re.sub(r'\*+(\n*)$', r'\1', l)
            sourcelines.append(l)
            l = l.lower()
            lowerlines.append(l)
            m = re.match('doi ?([0-9-/]+)', l)
            if len(ids) == 1 and m and m.lastgroup:
                ids.append(m.lastgroup)
        self.write_filtered('', '\n', ids, f)
        self.write_filtered('', ', ', citation, f)
        start = 0
        for author in authors:
            surname = self.text(author, 'foaf:surname')
            givenName = self.text(author, 'foaf:givenName')
            if not givenName:
                continue
            name = f"{surname} {givenName}".strip()
            for (newstart, l) in enumerate(sourcelines):
                if surname in l and givenName in l and len(l) > len(name):
                    name = l
                    if start < newstart:
                        start = newstart + 1
            f.write(name + '\n')
        f.write(f"\n# {title}\n\n")
        self.write_filtered('Tags: ', ', ', tags, f)
        lowertitle = title.lower()
        head_len = len(lowerlines) // 5
        if start > head_len:
            start = 0
        for (newstart, l) in enumerate(lowerlines[:head_len]):
            if lowertitle in l:
                start = newstart + 1
                break
            if 'аннотация' in l:
                start = newstart
                break
            if 'abstract' in l:
                start = newstart
        f.write('\n'.join(sourcelines[start:]))

    def write_filtered(self, prefix, delimiter, fields, f):
        fields = filter(None, fields)
        if fields:
            f.write(prefix + delimiter.join(fields) + '\n\n')
