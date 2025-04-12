import openai
import datetime

from statistics import mean, stdev

import parser

def log(info, debug = ''):
    print(str(datetime.datetime.now()).split('.')[0], info + '\n')
    # print(debug + '\n')

class Client:

    def __init__(self, cfg = {}):
        parser.extend_config('configs/llm.yaml', cfg)
        arguments = {
            'base_url': cfg.get('base_url', 'http://localhost:11434/v1/'),
            'api_key': 'EMPTY',
            'default_headers': {'Authorization': 'Bearer ' + cfg['token']} if 'token' in cfg else {}
        }
        self.client = openai.Client(**arguments)
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
        response = self.client.embeddings.create(input=input, model=model) #, options=options, keep_alive=-1)
        ems = response.data[0].embedding
        log(f'embed [{len(ems)}] ({mean(ems):.8f}, {stdev(ems):.8f}) <<< {model}')
        return ems
