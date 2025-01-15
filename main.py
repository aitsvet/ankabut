import sys
import yaml

import convert
import graph
import database
import pathlib
import scripts

def main(src, dst, cfg = None):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    if dst.is_dir():
        convert.from_pdf(src, dst)
    else:
        db = database.Load(src)
        if dst.suffix == '.html':
            graph.authors_keywords(db, dst)
        elif cfg:
            with open(cfg, 'r') as f:
                cfg = yaml.safe_load(f)
            scripts.repo[cfg['script']](db, cfg)
        db.save(dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
