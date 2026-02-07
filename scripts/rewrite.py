import pathlib

from generate import rewriter
    
def run(db, dst: pathlib.Path, cfg = {}):
    print(rewriter.New(db, cfg, dst).rewrite())
