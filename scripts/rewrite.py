import pathlib

import generator
    
def run(db, cfg, dst: pathlib.Path):
    print(generator.New(db, dst, cfg).rewrite())
