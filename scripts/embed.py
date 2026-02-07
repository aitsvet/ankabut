import pathlib
import sys

import embedder

def run(db, dst: pathlib.Path, cfg = {}):
    em = embedder.Index(db, dst, cfg)
    for input in sys.stdin:
       print('\n'.join(em.search(input.rstrip('\n'))))