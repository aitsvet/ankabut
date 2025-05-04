import pathlib

from generate import rewriter
    
def run(db, cfg, dst: pathlib.Path):
    print(rewriter.New(db, dst, cfg).rewrite())
