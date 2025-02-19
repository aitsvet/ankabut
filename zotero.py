from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from pathlib import Path

import re
import xml.etree.ElementTree as ET

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
    converter = PdfConverter(artifact_dict=create_model_dict())
    journals = root.findall('bib:Journal', nss)
    attachments = root.findall('z:Attachment', nss)
    for (i, article) in enumerate(root.findall('bib:Article', nss)):
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
        rendered = converter(source_path)
        source, _, _ = text_from_rendered(rendered)
        output = dst.joinpath(Path(source_path).with_suffix('.md').name)
        with open(output, 'w+') as f:
            lower = source.lower()
            start = 0
            for m in ['аннотация', 'abstract', title.lower()]:
                if m in lower and lower.index(m) > start:
                    start = lower.index(m)
            if start:
                for line in source[:start].splitlines():
                    m = re.match('doi ?([0-9-/]+)', line.lower())
                    if not doi and m.lastgroup:
                        doi = m.lastgroup
            f.write('\n'.join(filter(None, [url, doi])) + '\n\n')
            f.write(', '.join(filter('', [year, journal, volume, number, pages])) + '\n\n')
            for author in article.findall('bib:authors/rdf:Seq/rdf:li/foaf:Person', nss):
                names = [text(author, 'foaf:'+n) for n in ['surname', 'givenName']]
                f.write(' '.join(filter(None, names)) + '\n')
            f.write(f'\n# {title}\n\nTags: ')
            tags = [text(tag, 'rdf:value') for tag in article.findall('dc:subject/z:AutomaticTag', nss)]
            f.write(', '.join(filter(None, tags)) + '\n\n')
            if start and lower[start:].startswith(title.lower()):
                start += len(title)
            for line in source[start:].splitlines(True):
                if not any(c in line for c in ['=', '/']):
                    line = line.replace('**', '')
                    line = re.sub(r'^\*+', '', line)
                    line = re.sub(r'\*+(\n*)$', r'\1', line)
                f.write(line)
            print(f'Written {output}')
