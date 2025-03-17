import os
import sys
import yaml

import zotero
import graph
import database
import pathlib
import scripts
import pdf

def main(src, dst, cfg = {}):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    if not (dst.exists() or dst.suffix in ['.html', '.json', '.sqlite']):
        os.makedirs(dst, exist_ok=True)
    if dst.is_dir():
        if src.suffix == '.pdf':
            print(pdf.Reader().extract_markdown_from(src.as_posix()))
        else:
            zotero.load(src, dst)
    else:
        db = database.Load(src)
        if dst.suffix == '.html':
            graph.authors_keywords(db, dst)
        elif cfg:
            with open(cfg, 'r') as f:
                cfg = yaml.safe_load(f)
            scripts.repo[cfg['script']](db, cfg, dst)
        else:
            db.save(dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
