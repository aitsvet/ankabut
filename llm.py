# import logging
# import os

# # Set environment variable FIRST
# os.environ['OPENAI_LOG'] = 'debug'

# # Configure logging BEFORE any other imports
# logging.basicConfig(
#     level=logging.DEBUG,  # Set root to DEBUG to capture everything
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     force=True  # This is KEY - forces reconfiguration
# )

# # Now set specific loggers
# logging.getLogger('openai').setLevel(logging.DEBUG)
# logging.getLogger('openai._base_client').setLevel(logging.DEBUG)
# logging.getLogger('httpx').setLevel(logging.DEBUG)
# logging.getLogger('httpcore').setLevel(logging.DEBUG)
# logging.getLogger('h11').setLevel(logging.DEBUG)

import ssl
import httpx

OriginalClient = httpx.Client

class ExtraRootCertClient(OriginalClient):
    def __init__(self, *args, **kwargs):
        try:
            context = ssl.create_default_context()
            context.set_ciphers("DEFAULT:@SECLEVEL=2")
            context.load_verify_locations(cafile="./data/ssl.pem")
            kwargs["verify"] = context
        except Exception as e:
            pass
        super().__init__(*args, **kwargs)

httpx.Client = ExtraRootCertClient

import openai
import datetime

from statistics import mean, stdev

import parser

def log(info, debug = ''):
    print(str(datetime.datetime.now()).split('.')[0], info + '\n')
    # print(debug + '\n')

class Client:

    def __init__(self, cfg = {}):
        self.cfg = cfg.copy()
        parser.extend_config('configs/llm.yaml', self.cfg)
        arguments = {
            'base_url': cfg.get('base_url', 'http://localhost:11434/v1/'),
            'api_key': cfg.get('api_key', 'EMPTY'),
            'timeout': cfg.get('timeout', 3600.0)
        }
        self.client = openai.Client(**arguments)
        self.prompts = cfg.get('prompts', {})

    def chat(self, prompt, values):
        request = self.prompts[prompt]['template'].format(**values)
        messages = [{'role': 'user', 'content': request}]
        model = self.prompts[prompt]['model']
        max_tokens = self.prompts[prompt]['max_tokens']
        log(f"{prompt} [{len(request)}] >>> {model}", request)
        response = self.client.chat.completions.create(messages=messages, model=model, max_tokens=max_tokens)
        response = response.choices[0].message.content
        log(f"{prompt} [{len(response)}] <<< {model}", response)
        return response

    def embed(self, input):
        model = self.prompts.get('embed', {}).get('model')
        log(f"embed [{len(input)}] >>> {model}", input)
        response = self.client.embeddings.create(input=input, model=model)
        ems = response.data[0].embedding
        log(f"embed [{len(ems)}] ({mean(ems):.8f}, {stdev(ems):.8f}) <<< {model}")
        return ems
