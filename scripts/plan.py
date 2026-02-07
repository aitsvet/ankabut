import pathlib

from generate import planner
    
def run(db, dst: pathlib.Path, cfg = {}):
    print(planner.New(db, dst, cfg).plan())