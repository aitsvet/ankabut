import pathlib

from generate import writer
    
def run(db, dst: pathlib.Path, cfg = {}):
    print(writer.New(db, dst, cfg).write())