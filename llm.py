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
            'default_headers': {'Authorization': 'Bearer ' + cfg['token']} if 'token' in cfg else {},
            'timeout': cfg.get('timeout', 3600.0)
        }
        self.client = openai.Client(**arguments)
        self.prompts = cfg.get('prompts', {})

    def chat(self, prompt, values):
        request = self.prompts[prompt]['template'].format(**values)
        messages = [{'role': 'user', 'content': request}]
        model = self.prompts[prompt]['model']
        max_tokens = self.prompts[prompt]['max_tokens']
        log(f'{prompt} [{len(request)}] >>> {model}', request)
        response = self.client.chat.completions.create(messages=messages, model=model, max_tokens=max_tokens)
        response = response.choices[0].message.content
        log(f'{prompt} [{len(response)}] <<< {model}', response)
        return response

    def embed(self, input):
        model = self.prompts.get('embed', {}).get('model', 'bge-m3')
        log(f'embed [{len(input)}] >>> {model}', input)
        response = self.client.embeddings.create(input=input, model=model)
        ems = response.data[0].embedding
        log(f'embed [{len(ems)}] ({mean(ems):.8f}, {stdev(ems):.8f}) <<< {model}')
        return ems
