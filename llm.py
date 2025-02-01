import ollama
import datetime

from statistics import mean, stdev

import parse

def log(info, debug = ''):
    print(str(datetime.datetime.now()).split('.')[0], info + '\n')
    # print(debug + '\n')

class Client:

    def __init__(self, cfg = {}):
        parse.extend_config('configs/llm.yaml', cfg)
        self.headers = {'Authorization': 'Bearer ' + cfg['token']} if 'token' in cfg else {}
        self.client = ollama.Client(host=cfg.get('host', None), headers=self.headers)
        self.prompts = cfg['prompts']

    def chat(self, prompt, values):
        request = self.prompts[prompt]['template'].format(**values)
        messages = [{'role': 'user', 'content': request}]
        model = self.prompts[prompt]['model']
        options = self.prompts[prompt]['options']
        log(f'{prompt} [{len(request)}] >>> {model}', request)
        response = self.client.chat(messages=messages, model=model, options=options)
        response = response['message']['content']
        log(f'{prompt} [{len(response)}] <<< {model}', response)
        return response

    def embed(self, input):
        model = self.prompts['embed']['model']
        options = self.prompts['embed']['options']
        log(f'embed [{len(input)}] >>> {model}', input)
        response = self.client.embed(input=input, keep_alive=-1, model=model, options=options)
        ems = response['embeddings'][0]
        log(f'embed [{len(ems)}] ({mean(ems):.8f}, {stdev(ems):.8f}) <<< {model}')
        return ems
