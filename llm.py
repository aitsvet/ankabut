import yaml
import ollama

def log(s):
    print(s + '\n')

class Client:

    def __init__(self, cfg):
        with open(cfg, 'r') as f:
            self.prompts = yaml.safe_load(f)
        self.model = self.prompts['model']
        self.num_ctx = self.prompts['num_ctx']

    def chat(self, prompt, input):
        log('>>> ' + self.model)
        request = self.prompts[prompt].format(input=input)
        log(request)
        log('<<< ' + self.model)
        response = ollama.chat(model=self.model, options={'num_ctx': self.num_ctx},
                               messages=[{'role': 'user', 'content': request}])
        log(response['message']['content'])
        return response['message']['content']
