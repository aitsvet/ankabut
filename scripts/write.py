import pathlib

from generate import writer
    
def run(db, cfg, dst: pathlib.Path):
    print(writer.New(db, dst, cfg).write())