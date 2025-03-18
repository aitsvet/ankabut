from pathlib import Path

import re
import xml.etree.ElementTree as ET
import pdf

def attrib(elem, name, default = None):
    return elem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}' + name, default)

def load(src: Path, dst: Path):
    with open(src, 'r') as f:
        root = ET.fromstring(f.read())
    with open(src, 'r') as f:
        start = ET.iterparse(f, events=['start-ns'])
        nss = {key: value for _, (key, value) in start}
    def text(parent, path, default = None):
        elem = parent.findtext(path, default, nss)
        return elem.strip() if elem != default else default
    reader = pdf.Reader()
    journals = root.findall('bib:Journal', nss)
    attachments = root.findall('z:Attachment', nss)
    for article in root.findall('bib:Article', nss) + root.findall('rdf:Description', nss):
        partOf = article.find('dcterms:isPartOf', nss)
        journal = partOf.find('bib:Journal', nss)
        if journal is None:
            partOf = attrib(partOf, 'resource')
            journal = [j for j in journals if attrib(j, 'about') == partOf][0]
        volume = text(journal, 'prism:volume')
        volume = ('Т.' + volume) if volume else ''
        number = text(journal, 'prism:number')
        number = ('№' + number) if number else ''
        doi = text(journal, 'dc:identifier')
        journal = text(journal, 'dc:title')
        url = attrib(article, 'about')
        title = text(article, 'dc:title')
        year = text(article, 'dc:date')
        pages = text(article, 'bib:pages')
        pages = ('С.' + pages) if pages else ''
        link = article.find('link:link', nss)
        if link is None:
            continue
        link = attrib(link, 'resource')
        attachment = [a.find('rdf:resource', nss) for a in attachments if attrib(a, 'about') == link][0]
        source_path = src.parent.joinpath(attrib(attachment, 'resource')).as_posix()
        source = reader.extract_markdown_from(source_path)
        output = dst.joinpath(Path(source_path).with_suffix('.md').name)
        with open(output, 'w+') as f:
            sourcelines = []
            lowerlines = []
            for line in source.splitlines():
                l = line
                if not any(c in line for c in ['=', '/']):
                    l = l.replace('**', '').replace('©', '')
                    l = re.sub(r'^\*+', '', l)
                    l = re.sub(r'\*+(\n*)$', r'\1', l)
                sourcelines.append(l)
                lowerlines.append(l.lower())
            for line in sourcelines:
                m = re.match('doi ?([0-9-/]+)', line.lower())
                if not doi and m and m.lastgroup:
                    doi = m.lastgroup
            f.write('\n'.join(filter(None, [url, doi])) + '\n\n')
            f.write(', '.join(filter(None, [year, journal, volume, number, pages])) + '\n\n')
            for author in article.findall('bib:authors/rdf:Seq/rdf:li/foaf:Person', nss):
                surname = text(author, 'foaf:surname')
                givenName = text(author, 'foaf:givenName')
                name = f'{surname} {givenName}'
                for line in sourcelines:
                    if surname in line and givenName in line and len(line) > len(name):
                        name = line
                f.write(name + '\n')
            f.write(f'\n# {title}\n\nTags: ')
            tags = [text(tag, 'rdf:value') for tag in article.findall('dc:subject/z:AutomaticTag', nss)]
            f.write(', '.join(filter(None, tags)) + '\n\n')
            start = 0
            lowertitle = title.lower()
            for (newstart, line) in enumerate(lowerlines[:len(lowerlines) // 5]):
                if lowertitle in line:
                    start = newstart + 1
                    break
                if 'аннотация' in line:
                    start = newstart
                    break
                if 'abstract' in line:
                    start = newstart
            f.write('\n'.join(sourcelines[start:]))
            print(f'Written {output}')
