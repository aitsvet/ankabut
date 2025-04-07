import pathlib
import sys

import embedder

def run(db, cfg, dst: pathlib.Path):
    em = embedder.Index(db, cfg, dst)
    for input in sys.stdin:
       print('\n'.join(em.search(input.rstrip('\n'))))