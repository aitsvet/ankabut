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
    attachments = root.findall('z:Attachment/rdf:resource', nss)
    for (i, article) in enumerate(root.findall('bib:Article', nss)):
        journal = text(article, 'dcterms:isPartOf/bib:Journal/dc:title')
        if not journal:
            journal = text(journals[i], 'dc:title')
            volume = text(journals[i], 'prism:volume')
            number = text(journals[i], 'prism:number')
        url = attrib(article, 'about')
        doi = text(article, 'dcterms:isPartOf/bib:Journal/dc:identifier')
        if not doi:
            doi = text(journals[i], 'dc:identifier')
        title = text(article, 'dc:title')
        year = text(article, 'dc:date')
        language = text(article, 'z:language')
        pages = text(article, 'bib:pages')
        source_path = src.parent.joinpath(attrib(attachments[i], 'resource')).as_posix()
        rendered = converter(source_path)
        source, _, _ = text_from_rendered(rendered)
        output = dst.joinpath(Path(source_path).with_suffix('.md').name)
        with open(output, 'w+') as f:
            lower = source.lower()
            start = max([(lower.index(m), m) for m in ['аннотация', 'abstract', title.lower()]])
            for line in source[:start].splitlines():
                m = re.match('doi ?([0-9-/]+)', line.lower())
                if not doi and m.lastgroup:
                    doi = m.lastgroup
            f.write('\n'.join(filter(None, [url, doi])) + '\n\n')
            f.write(', '.join(filter(None, [year, language, journal, volume, number, pages])) + '\n\n')
            for author in article.findall('bib:authors/rdf:Seq/rdf:li/foaf:Person', nss):
                names = [text(author, 'foaf:'+n) for n in ['surname', 'givenName']]
                f.write(' '.join(filter(None, names)) + '\n')
            f.write(f'\n# {title}\n\n')
            tags = [text(tag, 'rdf:value') for tag in article.findall('dc:subject/z:AutomaticTag', nss)]
            f.write(', '.join(filter(None, tags)) + '\n\n')
            if lower[start:].startswith(title.lower()):
                start += len(title)
            for line in source[start:].splitlines():
                f.write(line if any(c in line for c in ['=', '-', '/']) else line.replace('*', ''))
            print(f'Written {output}')
