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
        for article in self.all('bib:Article') + self.all('rdf:Description'):
            self.load_article(article, src, dst)

    def all(self, elem):
        return self.root.findall(elem, self.nss)

    def text(self, parent, path, default = None):
        elem = parent.findtext(path, default, self.nss)
        return elem.strip() if elem != default else default

    def load_article(self, article, src: Path, dst: Path):
        link = article.find('link:link', self.nss)
        if link is None:
            return
        link = attrib(link, 'resource')
        year = self.text(article, 'dc:date')
        authors = article.findall('bib:authors/rdf:Seq/rdf:li/foaf:Person', self.nss)
        firstAuthor = self.text(authors[0], 'foaf:surname')
        title = self.text(article, 'dc:title')
        dstname = parser.trim_filename(f"{year} {firstAuthor} {title}")
        output = dst.joinpath(Path(dstname).with_suffix('.md').name)
        if output.exists():
            return
        partOf = article.find('dcterms:isPartOf', self.nss)
        journal = partOf.find('bib:Journal', self.nss)
        if journal is None:
            partOf = attrib(partOf, 'resource')
            journal = [j for j in self.journals if attrib(j, 'about') == partOf][0]
        ids = [attrib(article, 'about'), self.text(journal, 'dc:identifier')]
        volume = f"Т.{v}' if (v := self.text(journal, 'prism:volume')) else '"
        number = f"№{n}' if (n := self.text(journal, 'prism:number')) else '"
        pages = f"С.{p}' if (p := self.text(article, 'bib:pages'))  else '"
        journal = self.text(journal, 'dc:title')
        citation = [year, journal, volume, number, pages]
        tags = [self.text(tag, 'rdf:value') for tag in article.findall('dc:subject/z:AutomaticTag', self.nss)]
        attachment = [a.find('rdf:resource', self.nss) for a in self.attachments if attrib(a, 'about') == link][0]
        source_path = src.parent.joinpath(attrib(attachment, 'resource')).as_posix()
        source = self.reader.md_from(source_path)
        with open(output, 'w+') as f:
            self.save_article(ids, citation, authors, title, tags, source, f)
        print(f"Written {output}")

    def save_article(self, ids, citation, authors, title, tags, source, f):
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
        f.write('\n'.join(filter(None, ids)) + '\n\n')
        f.write(', '.join(filter(None, citation)) + '\n\n')
        for author in authors:
            surname = self.text(author, 'foaf:surname')
            givenName = self.text(author, 'foaf:givenName')
            name = f"{surname} {givenName}"
            for l in sourcelines:
                if surname in l and givenName in l and len(l) > len(name):
                    name = l
            f.write(name + '\n')
        f.write(f"\n# {title}\n\nTags: {", ".join(filter(None, tags))}\n\n")
        start = 0
        lowertitle = title.lower()
        for (newstart, l) in enumerate(lowerlines[:len(lowerlines) // 5]):
            if lowertitle in l:
                start = newstart + 1
                break
            if 'аннотация' in l:
                start = newstart
                break
            if 'abstract' in l:
                start = newstart
        f.write('\n'.join(sourcelines[start:]))
