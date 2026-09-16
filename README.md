# PDF Knowledge Base for GitHub Pages

A GitHub-ready PDF knowledge library designed for both humans and AI agents.

## What it does

- Reads PDFs from a folder on your Windows PC.
- Copies them into `pdfs/`.
- Extracts searchable text into `text/`.
- Generates `library.json`, a machine-readable catalogue.
- Generates a searchable `index.html`.
- Generates `ai.txt`, a simple AI-oriented discovery file.
- Creates stable URLs for every PDF and extracted text file.
- Can automatically commit and push changes to GitHub.

## Requirements

- Windows 10/11
- Python 3.10+
- Git
- A GitHub repository with GitHub Pages enabled

Install the Python dependency:

```bash
python -m pip install -r requirements.txt
```

## First-time setup

1. Create a GitHub repository.
2. Copy this project into the repository.
3. Edit `config.json`.
4. Put your PDFs in the local source folder specified in `config.json`.
5. Run:

```bash
python generate_library.py
```

6. Review the generated site locally by opening `index.html`.
7. Commit and push:

```bash
git add .
git commit -m "Update PDF knowledge library"
git push
```

## Automatic update on Windows

After Git and Python are configured, you can simply run:

```text
update_library.bat
```

It will:

1. Scan your local PDF folder.
2. Synchronize the PDFs.
3. Extract text.
4. Generate the AI index.
5. Commit the changes.
6. Push them to GitHub.

## AI Agent access

Give the AI Agent the root GitHub Pages URL:

```text
https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/
```

The agent can discover the catalogue from:

```text
library.json
```

and the AI-oriented discovery document from:

```text
ai.txt
```

Each document also has:

```text
pdfs/<document>.pdf
text/<document>.txt
```

The extracted text is intended to make document retrieval easier for systems that cannot efficiently process PDF files directly.

## Important

GitHub Pages is public unless your GitHub setup provides an access-controlled publishing method. Do not place confidential, personal, proprietary, or restricted documents in a public repository.

For a private corporate knowledge base, use an authenticated hosting/storage solution instead.


## AI Agent access — important

The site is designed so an AI Agent does **not** need search-engine indexing or directory browsing. The generated catalogue explicitly lists every document and its direct text/PDF URLs.

Machine-readable entry points:

```text
library.json
api/documents.json
ai.txt
llms.txt
sitemap.xml
robots.txt
```

Give the Agent the root GitHub Pages URL and instruct it to start with `llms.txt` or `library.json`. For relevant documents, it should retrieve the linked `text/*.txt` file for searchable text and use the `pdfs/*.pdf` file when the original PDF is required.

Set `site_url` in `config.json` to the final GitHub Pages URL before publishing.
