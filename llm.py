import yaml
import ollama
import statistics

def log(s):
    return
    print(s + '\n')

class Client:

    def __init__(self, cfg):
        try:
            with open('configs/llm.yaml', 'r') as f:
                for k, v in yaml.safe_load(f).items():
                    if k not in cfg:
                        cfg[k] = v
        except: pass
        self.headers = {'Authorization': 'Bearer ' + cfg['token']} if 'token' in cfg else {}
        self.client = ollama.Client(host=cfg.get('host', None), headers=self.headers)
        self.model = cfg['model']
        self.options = { 'num_ctx': cfg['num_ctx'] }
        self.prompts = cfg['prompts']

    def chat(self, prompt, values):
        log('>>> ' + self.model)
        request = self.prompts[prompt].format(**values)
        log(request)
        log('<<< ' + self.model)
        messages = [{'role': 'user', 'content': request}]
        response = self.client.chat(model=self.model, options=self.options, messages=messages)
        log(response['message']['content'])
        return response['message']['content']

    def embed(self, input):
        log('>>> ' + input)
        log('<<< ' + self.model)
        response = self.client.embed(model=self.model, input=input, options=self.options, keep_alive=-1)
        ems = response['embeddings'][0]
        log(f'{len(ems), statistics.mean(ems), statistics.stdev(ems)} ')
        return response['embeddings'][0]
