import sys

from ollama import chat, embed
from ollama import ChatResponse, EmbedResponse

with open(sys.argv[1], 'r') as f:
    prompt = f.read()

response: ChatResponse = chat(
    model='rscr/ruadapt_qwen2.5_32b:Q4_K_M',
    messages=[
    {
        'role': 'user',
        'content': prompt + input,
    },
])
print(response['message']['content'])