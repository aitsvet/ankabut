import pathlib

import rewriter
    
def run(db, cfg, dst: pathlib.Path):
    print(rewriter.New(db, dst, cfg).rewrite())
