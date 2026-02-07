import os
import sys
import yaml

import zotero
import database
import pathlib
import scripts
import pdf

def main(src, dst, cfg = {}):
    if cfg:
        with open(cfg, 'r') as f:
            cfg = yaml.safe_load(f)
    dst = pathlib.Path(dst)
    if not dst.exists():
        if dst.suffix.lower() in ['.html', '.json', '.sqlite', '.md', '.pdf']:
            os.makedirs(dst.parent, exist_ok=True)
        else:
            os.makedirs(dst, exist_ok=True)
    src = pathlib.Path(src)
    if src.suffix.lower() == '.rdf':
        zotero.Convert(src, dst, cfg)
    elif src.suffix.lower() == '.pdf':
        pdf.Reader(cfg).convert(src, dst)
    else:
        db = database.Load(src)
        if cfg:
            scripts.repo[cfg['script']](db, dst, cfg)
        else:
            db.save(dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
