import importlib
import os

repo = {}
script_files = [f for f in os.listdir(os.path.dirname(__file__)) 
                if f.endswith('.py') and f != '__init__.py']
for script_file in script_files:
    module_name = script_file[:-3]
    module = importlib.import_module(f'scripts.{module_name}')
    repo[script_file] = module.run