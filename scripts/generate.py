import pathlib

import generator
    
def run(db, cfg, dst: pathlib.Path):
    gen = generator.New(db, dst, cfg)
    gen.generate()
    print(gen.build('generate', cfg['title'], 'generate'))