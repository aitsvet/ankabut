import re

def author_name(title):
    return next((w.capitalize() for w in re.split(r'[\s,.]+', title) if len(w) > 3), None)

def keywords(line):
    return [kw.strip().lower() for kw in re.split(r'[,.]+', line) if kw]
