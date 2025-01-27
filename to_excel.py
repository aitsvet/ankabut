import jq
import sys
import json
import pandas as pd

with open(sys.argv[1], 'r') as f:
    json_data = json.load(f)

query = '[.[].docs[]] | group_by(.path) | map({path: .[0].path, title: .[0].title, keywords: .[0].keywords, llm: map(.llm)})'
data = jq.compile(query).input(json_data).all()

df = pd.json_normalize(data)
df_unnested = df['llm'].apply(lambda x: pd.Series({f'llm_{i}_{k}': item[k] for i, item in enumerate(x) for k in ['title', 'keywords', 'abstract']}))

result = pd.concat([df.drop(columns=["llm"]), df_unnested], axis=1)
result.to_excel(sys.argv[2], index=False)