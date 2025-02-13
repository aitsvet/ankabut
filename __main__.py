import os
import sys
import yaml

import zotero
import graph
import database
import pathlib
import scripts

def main(src, dst, cfg = {}):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    if not (dst.exists() or dst.suffix in ['.html', '.json', '.sqlite']):
        os.makedirs(dst, exist_ok=True)
    if dst.is_dir():
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
