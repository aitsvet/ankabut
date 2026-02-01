# Ankabut

An automated LLM prompting framework for:
1. [preprocessing literature items into a uniform structure](#preprocessing-journal-articles);
2. [extracting content and metadata from preprocessed articles](#extracting-content-and-metadata-from-articles);
3. [indexing and searching with LLM embeddings](#indexing-and-searching-with-llm-embeddings);
4. [generating new article structure plans](#generating-new-article-structure-plans);
5. [generating article content for specified plan](#generating-article-content-for-specified-plan).

## Preprocessing literature items

```bash
python . "<src>.rdf" "<dst dir>"

"<src>.rdf" - path to source Zotero RDF file containing links to PDF attachments
"<dst dir>" - destination directory where extracted Markdown files shall be stored
```

1. Parses Zotero RDF file containing item citations.
2. Parses linked PDF files via [marker-pdf](https://github.com/datalab-to/marker).
3. Stores parsed item content (without images) in the following Markdown structure:

```Markdown
<item id (DOI, URL, etc)>
...
<item id (DOI, URL, etc)>

<year of publication> <journal name> <issue> <volume> <etc.>

<author name> <author title> <institution> <etc.>
...
<author name> <author title> <institution> <etc.>

# <item title>

Tags: <from Zotero> ...

[Abstract. ...]

[Keywords: ...]

[## <section title>]

<section content>
...
<section content>

[
## (References|Literature|etc)

[1. ] <Author>, <Title> etc

...

[N. ] <Author>, <Title> etc
]
```

## Extracting content and metadata from literature items

```bash
python . "<src dir>" "<dst>.json"

"<src dir>" - source directory containing extracted Markdown files
"<dst>.json" - destination JSON file where item content and metadata shall be stored
```

1. Parses literature items in Markdown format described above.
2. Stores all literature items in the following JSON format:

```JSON
{
    "items": [
        {
            "ids": [ "DOI", "URL", "etc" ],
            "year": "2025",
            "authors": [
                "Author Name, Title, Institution", // ...
            ],
            "title": "<item title>",
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
python . "<src>.json" "<dst>.json" configs/embed.yaml

"<src>.json" - source JSON file containing item content and metadata
"<dst>.json" - destination JSON file to contain both items and embedding vectors
```

1. Retrieves embeddings for each paragraph of each section of each item in the source JSON file from an LLM, cofigured in [`configs/embed.yaml`](configs/embed.yaml).
2. Stores embeddings along with item contents and metadata into destination JSON file.

```bash
echo 'search query' | python . "<dst>.json" . configs/embed.yaml

"<dst>.json" - JSON file to contain both items and embedding vectors
```

1. Reads item contents and metadata along with paragraph embeddings from source JSON file.
2. Retrieves embedding of the search query using an LLM, cofigured in [`configs/embed.yaml`](configs/embed.yaml).
3. Runs a vector search using the index build from source paragraph embeddings.
4. Retrieves the content of corresponding paragraphs from the source JSON file.
5. Writes to standard output relevant search results grouped by source:

```JSON
{
Из источника <n>. <author> (<year>) <title>

<relevant section>

<relevant section>
}
```

```bash
python . "<src>.json" "<dst>.html" configs/analyze.yaml

"<src>.json" - source JSON file containing both items and embedding vectors
"<dst>.html" - destination HTML file to contain item graph and similarity report
```

1. Builds a graph of items (represented by `year`), author names and keywords as configured in [`configs/analyze.yaml`](configs/analyze.yaml).
2. Prints `max_samples` pairs of paragraphs from source documents having least embedding similarity.
3. Plots a heatmap of cosine distance beetween pairs of paragraph embeddings.

## Generating new article structure plans

```bash
python . "<src>.json" "<dst>.json" configs/plan.yaml

"<src>.json" - source JSON file containing source item content and metadata
"<dst>.json" - target JSON file to contain new article structure plan
```

1. Reads `<dst>.json` (you can copy [`data/template.json`](data/template.json) as an example).
2. Starts with an article structure plan specified in last document of `<dst>.json`.
3. Starts with a first item in `<src>.json` not in citation list of last document of `<dst>.json`.
3. For each item in `<src>.json` uses the LLM specified in [`configs/plan.yaml`](configs/plan.yaml) to refine the plan:
    1. Collects item content paragraphs in each section.
    2. In case the collected content overfits the specified LLM context size, summarises the collected content.
    3. Requests the specified LLM for a new version of the plan basing on the current version the plan and current article content.
    4. Stores the new plan as new document of `<dst>.json` along with all processed articles in the new document's citation list.
    5. Prints the updated plan to standard output.

## Generating article content for specified plan

```bash
python . "<src>.json" "<dst>.json" configs/write.yaml

"<src>.json" - source JSON file containing source item content, embeddings and metadata
"<dst>.json" - target JSON file to contain new article structure plan and generated content
```

1. Starts with an article structure plan specified in last document of `<dst>.json`.
2. For each section of the plan uses the LLM specified in [`configs/write.yaml`](configs/write.yaml) to generate section content:
    1. Collects section headers on a path from structure top to current section.
    2. Uses the search index to retrieve the paragraphs from source articles relevant to collected section headers.
    3. Collects all article section headers along with their content if present.
    4. Requests the specified LLM for new content of the current section basing on the collected paragraphs and present article content.
    5. Stores the resulting section in last document of `<dst>.json` along with all source articles in the new document's citation list.
    6. Prints the generated section to standard output.

## Rewriting article content

```bash
python . "<src>.json" "<dst>.json" configs/rewrite.yaml

"<src>.json" - source JSON file containing source item content, embeddings and metadata
"<dst>.json" - target JSON file to contain rewritten article content
```

1. Starts with an article specified in last document of `<dst>.json`.
2. For each section of the article uses the LLM specified in [`configs/write.yaml`](configs/write.yaml) to generate new section content:
    1. Collects section headers on a path from structure top to current section, then appends current section content.
    2. Uses the search index to retrieve the paragraphs from source articles relevant to collected section headers and content.
    3. Requests the specified LLM for new content of the current section basing on the collected paragraphs and present section content.
    4. Stores the resulting section in last document of `<dst>.json` along with all source articles in the new document's citation list.
    5. Prints the generated section to standard output.
