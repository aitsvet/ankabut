# Ankabut

An automated LLM prompting framework for:
1. [preprocessing journal articles into a uniform structure](#preprocessing-journal-articles);
2. [extracting content and metadata from preprocessed articles](#extracting-content-and-metadata-from-articles);
3. [indexing and searching with LLM embeddings](#indexing-and-searching-with-llm-embeddings);
4. [generating new article structure plans](#generating-new-article-structure-plans);
5. [generating article content for specified plan](#generating-article-content-for-specified-plan).

## Preprocessing journal articles

```bash
python . "<src>.rdf" "<dst dir>"

"<src>.rdf" - path to source Zotero RDF file containing links to PDF attachments
"<dst dir>" - destination directory where preprocessed article files shall be stored
```

1. Parses Zotero RDF file containing article citations.
2. Parses linked PDF files via [marker-pdf](https://github.com/VikParuchuri/marker).
3. Stores parsed article content (without images) in the following Markdown structure:

```Markdown
<article id (DOI, URL, etc)>
...
<article id (DOI, URL, etc)>

<year of publication> <journal name> <issue> <volume> etc

<author name> <author title> <institution> etc
...
<author name> <author title> <institution> etc

# <article title>

[Abstract. ...]

[Keywords: ...]

[## <section title>]

<section content>
...
<section content>

[
## (References|Literature|etc)

[1. ] Author, Title ...

...

[N. ] Author, Title ...
]
```

## Extracting content and metadata from articles

```bash
python . "<src dir>" "<dst>.json"

"<src dir>" - source directory containing Markdown article files
"<dst>.json" - destination JSON file where article content and metadata shall be stored
```

1. Parses articles in Markdown format described above.
2. Stores all articles in the follfwing JSON format:

```JSON
{
    "articles": [
        {
            "ids": [ "DOI", "URL", "etc" ],
            "year": "2025",
            "authors": [
                "Author Name, Title, Institution", // ...
            ],
            "title": "<article title>",
            "abstract": "<...>",
            "keywords": [ "keyword", /* ... */ ],
            "sections": [
                {
                    [ "title": "<section title>", ]
                    "content": [
                        "<paragraph>", // ...
                    ]
                }, // ...
            ],
            "citations": [
                "Author, Title ...", // ...
            ]
        }
    ],
    "authors": {
        "<author name>": [
            "DOI", "DOI", "DOI", // ...
        ]
    },
    "keywords": {
        "keyword": 1, // ... occurence count
    },
    "citations": [
        "Author, Title ...", // ...
    ],
    "paragraph_ids": [
        "<DOI|URL|etc>:<section index>:<paragraph index>", // ...
    ]
}
```

## Indexing and searching with LLM embeddings

```bash
python . "<src>.json" "<dst>.idx" configs/embed.yaml

"<src>.json" - source JSON file containing article content and metadata
"<dst>.idx" - non-existing destination search index file
```

1. Retrieves embeddings for each paragraph of each section of each article in the source JSON file from an LLM, cofigured in [`configs/embed.yaml`](configs/embed.yaml).
2. Builds a [Faiss](https://github.com/facebookresearch/faiss) search index from those embeddings and stores to the destination file.

```bash
echo "query" | python . "<src>.json" "<src>.idx" configs/embed.yaml

"<src>.json" - source JSON file containing article content and metadata
"<src>.idx" - existing search index file
```

1. Reads the search query from the standard input.
2. Retrieves embedding of the search query using an LLM, cofigured in [`configs/embed.yaml`](configs/embed.yaml).
3. Runs a [Faiss](https://github.com/facebookresearch/faiss) search in the source index file.
4. Retrieves the content of corresponding paragraphs from the source JSON file.
5. Writes to standard output search results in the following JSON format:

```JSON
{
    "query": "<query>",
    "model": "<embedding model name>",
    "source": "<src>.json",
    "index": "<src>.idx",
    "results": [
        {
            "id": "<DOI|URL|etc>:<section index>:<paragraph index>",
            "distance": 0.54321098, // distance between query and paragraph
            "content": "<paragraph>"
        }, // ...  
    ]
}
```

## Generating new article structure plans

```bash
python . "<src>.json" "<src>.idx" configs/plan.yaml

"<src>.json" - source JSON file containing article content and metadata
"<src>.idx" - existing search index file
```

1. Starts with an article structure plan specified in [`configs/plan.yaml`](configs/plan.yaml).
2. Walks through articles in the source JSON file in order specified in the config.
3. For each articles uses the specified LLM to refine the plan:
    1. If the current article has the `plan` field in the source JSON, uses it as the current plan and continues with next acticle.
    2. Collects article content paragraphs in each section.
    3. In case the collected content overfits the specified LLM context size,  summarises the collected content.
    4. Requests the specified LLM for a new version of the plan basing on the current version the plan and current article content.
    5. Stores the `plan` field of current article in source JSON with the new version of the plan.
4. Writes the resulting plan to standard output.

## Generating article content for specified plan

```bash
python . "<src>.json" "<src>.idx" configs/generate.yaml

"<src>.json" - source JSON file containing article content and metadata
"<src>.idx" - existing search index file
```

1. Starts with an article structure plan specified in [`configs/generate.yaml`](configs/generate.yaml).
2. For each section of the plan uses the specified LLM to generate section content:
    1. Collects section headers on a path from structure top to current section.
    2. Uses the search index to retrieve the paragraphs from source articles relevant to collected section headers.
    3. Collects all article section headers along with their content if present.
    4. Requests the specified LLM for new content of the current section basing on the collected paragraphs and present article content.
    5. Stores the resulting section in the source JSON along other source article content and metadata.
3. Writes the resulting article to standard output.
