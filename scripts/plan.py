import pathlib

from generate import planner
    
def run(db, cfg, dst: pathlib.Path):
    print(planner.New(db, dst, cfg).plan())