import yaml
import ollama

def log(s):
    print(s + '\n')

class Client:

    def __init__(self, cfg):
        try:
            with open('configs/llm.yaml', 'r') as f:
                for k, v in yaml.safe_load(f).items():
                    if k not in cfg:
                        cfg[k] = v
        except: pass
        self.client = ollama.Client(host=cfg.get('host', None),
                                    headers={'Authorization': 'Bearer ' + cfg['token']} if 'token' in cfg else {})
        self.model = cfg['model']
        self.num_ctx = cfg['num_ctx']
        self.prompts = cfg['prompts']

    def chat(self, prompt, values):
        log('>>> ' + self.model)
        request = self.prompts[prompt].format(**values)
        log(request)
        log('<<< ' + self.model)
        response = self.client.chat(model=self.model, options={'num_ctx': self.num_ctx},
                                    messages=[{'role': 'user', 'content': request}])
        log(response['message']['content'])
        return response['message']['content']
