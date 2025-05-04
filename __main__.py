import os
import sys
import yaml

import zotero
import database
import pathlib
import scripts
import pdf

def main(src, dst, cfg = {}):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    if not (dst.exists() or dst.suffix in ['.html', '.json', '.sqlite', '.md']):
        os.makedirs(dst, exist_ok=True)
    if src.suffix == '.rdf':
        zotero.load(src, dst)
    elif src.suffix == '.pdf':
        dst.write_bytes(pdf.Reader().extract_markdown_from(src.as_posix()))
    else:
        db = database.Load(src)
        if cfg:
            with open(cfg, 'r') as f:
                cfg = yaml.safe_load(f)
            scripts.repo[cfg['script']](db, cfg, dst)
        else:
            db.save(dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
